import os
import time
from datetime import datetime, timezone
from typing import List
from urllib.parse import urljoin

from setuptools.extern import names

from common.BackupConfig import BackupConfig
from schemas import BackupItem, BackupStorage, S3StorageDTO, S3BackupFileDTO
from services.S3Client import S3Client
import logging

from services.backup_files import get_backup_file_by_details_service, create_s3_backup_file_service, \
    update_s3_backup_file_service
from services.s3_storages import create_or_get_storage_by_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаём обработчик для записи в файл
file_handler = logging.FileHandler('backup.log')
file_handler.setLevel(logging.INFO)

# Создаём обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Создаём форматтер и добавляем его к обработчикам
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

async def is_extension_included_in_backup(extension: str, include: List[str], exclude: List[str]) -> bool:
    # Если расширение есть в списке include, возвращаем True
    if include and extension in include:
        return True

    # Если список include пустой и расширение не в exclude, возвращаем True
    if not include and extension not in exclude:
        return True

    # Во всех остальных случаях возвращаем False
    return False


async def get_or_register_storage_dto(storage: BackupStorage) -> S3StorageDTO:
    storage_dto = S3StorageDTO(
        name=storage.name,
        url=storage.url,
        access_key=storage.access_key,
        secret_key=storage.secret_key,
    )
    return create_or_get_storage_by_name(s3_storage=storage_dto)


async def register_uploaded_file(storage_id: int, upload_file_dto: S3BackupFileDTO) -> None:
    if upload_file_dto.id is None:
        create_s3_backup_file_service(backup_file=upload_file_dto, storage_id=storage_id)
    else:
        update_s3_backup_file_service(upload_file_dto.id, upload_file_dto)


async def get_upload_file_info_from_db(storage: S3StorageDTO, item: BackupItem, top_level_path: str) -> S3BackupFileDTO:
    full_path, filename = os.path.split(item.path)
    # В БД храним путь БЕЗ top_level (БЕЗ storage.items.path) и без имени файла
    path = full_path.replace(top_level_path, '')
    backup_file_dto = get_backup_file_by_details_service(
        storage_id=storage.id,
        path=path,
        file_name=filename,
    )
    return backup_file_dto


async def create_upload_file_info(storage: S3StorageDTO, backup_item: BackupItem, top_level_path: str) -> S3BackupFileDTO:
    file_path, file_name = os.path.split(backup_item.path)
    file_size = os.path.getsize(backup_item.path)
    file_time = os.path.getmtime(backup_item.path)
    file_time_utc = datetime.fromtimestamp(file_time, tz=timezone.utc)
    path = file_path.replace(top_level_path, '')
    backup_file_dto = S3BackupFileDTO(
        storage_id = storage.id,
        path=path,
        file_name=file_name,
        file_size=file_size,
        file_time=file_time_utc,
    )
    return backup_file_dto

async def backup_item(storage: S3StorageDTO, client: S3Client, item: BackupItem, top_level_path: str):
    """Рекурсивная"""
    if item.is_directory:
        logger.info(f'Processing item.path')
        folder_elements = os.listdir(item.path)
        for folder_element in folder_elements:
            # folder_element привести к виду BackupItem:
            next_backup_item = BackupItem(
                name=item.name,
                bucket=item.bucket,
                path=os.path.join(item.path, folder_element),
                include=item.include,
                exclude=item.exclude,
            )
            await backup_item(storage=storage, client=client, item=next_backup_item, top_level_path=top_level_path)
    elif item.is_file:
        object_name=item.path.replace(top_level_path, '')
        extension = os.path.splitext(item.path)[1][1:].lower()
        if await is_extension_included_in_backup(extension=extension, include=item.include, exclude=item.exclude):
            upload_file_dto: S3BackupFileDTO = await get_upload_file_info_from_db(
                storage=storage,
                item=item,
                top_level_path=top_level_path
            )
            if upload_file_dto is None:
                upload_file_dto = await create_upload_file_info(storage=storage, backup_item=item, top_level_path=top_level_path)
            logger.info(f'Uploading {object_name}')
            item_path_struct_time = time.gmtime(os.path.getmtime(item.path))
            item_path_datetime = datetime(*item_path_struct_time[:6])
            if os.path.getsize(item.path) != upload_file_dto.file_size or item_path_datetime != upload_file_dto.file_time.replace(microsecond=0):

                await client.upload_file(
                    bucket_name=item.bucket,
                    file_path=item.path,
                    object_name=object_name,
                )
            # Регистрируем файл в БД
            await register_uploaded_file(storage_id=storage.id, upload_file_dto=upload_file_dto)
            logger.info(f'{object_name} uploaded to {item.bucket}')


async def backup_storage(storage: BackupStorage, item_name: str | None = None):
    logger.info(f'Processing storage {storage.name}')
    # Регистрируем storage в БД
    storage_dto = await get_or_register_storage_dto(storage=storage)
    # Создаём s3 клиента
    client = S3Client(
        access_key=storage.access_key,
        secret_key=storage.secret_key,
        endpoint_url=storage.url,
    )
    for item in storage.items:
        if item_name is None or item.name.lower == item_name.lower():
            await backup_item(storage=storage_dto, client=client, item=item, top_level_path=item.path)


async def backup(storage_name: str | None = None, item_name: str | None = None):
    backup_config = BackupConfig()
    logger.info('Config loaded')
    for s3_storage in backup_config.backup_storages:
        if storage_name is None or s3_storage.name.lower() == storage_name.lower():
            await backup_storage(s3_storage, item_name)
    logger.info('Done!')
