import os
from typing import List

from common.BackupConfig import BackupConfig
from schemas import BackupItem, BackupStorage
from services.S3Client import S3Client


async def is_extension_included_in_backup(extension: str, include: List[str], exclude: List[str]) -> bool:
    # Если расширение есть в списке include, возвращаем True
    if include and extension in include:
        return True

    # Если список include пустой и расширение не в exclude, возвращаем True
    if not include and extension not in exclude:
        return True

    # Во всех остальных случаях возвращаем False
    return False


async def backup_item(client: S3Client, item: BackupItem, top_level_path: str):
    """Рекурсивная"""
    if item.is_directory:
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
            await backup_item(client, next_backup_item, top_level_path)
    elif item.is_file:
        object_name=item.path.replace(top_level_path, '')
        extension = os.path.splitext(item.path)[1][1:].lower()
        if await is_extension_included_in_backup(extension=extension, include=item.include, exclude=item.exclude):
            await client.upload_file(
                bucket_name=item.bucket,
                file_path=item.path,
                object_name=object_name,
            )


async def backup_storage(storage: BackupStorage, item_name: str | None = None):
    client = S3Client(
        access_key=storage.access_key,
        secret_key=storage.secret_key,
        endpoint_url=storage.url,
    )
    for item in storage.items:
        if item_name is None or item.name.lower == item_name.lower():
            await backup_item(client=client, item=item, top_level_path=item.path)


async def backup(storage_name: str | None = None, item_name: str | None = None):
    backup_config = BackupConfig()
    for s3_storage in backup_config.backup_storages:
        if storage_name is None or s3_storage.name.lower() == storage_name.lower():
            await backup_storage(s3_storage, item_name)
