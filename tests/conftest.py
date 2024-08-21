import os
import random

import pytest
from alembic import command
from alembic.config import Config

from common.settings import ROOT_DIR, settings
from db.engine import Session
from db.models import S3StorageOrm, BackupFileOrm
from repositories.backup_files import create_backup_file
from repositories.s3_storages import create_storage
from schemas import S3StorageDTO, S3BackupFileDTO, S3BackupFileRelDTO, S3StorageRelDTO

TEST_BACKUP_DIR = os.path.join(ROOT_DIR, 'test_data')

@pytest.fixture
def apply_migrations():
    db_path = settings.TEST_DB_DSN.replace('sqlite:///', '')
    assert 'test' in os.path.basename(db_path).lower(), 'Попытка использовать не тестовую SQLite базу данных.'

    alembic_cfg = Config(str(ROOT_DIR / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(ROOT_DIR / 'alembic'))
    command.downgrade(alembic_cfg, 'base')
    command.upgrade(alembic_cfg, 'head')

    yield command, alembic_cfg

    # command.downgrade(alembic_cfg, 'base')
    # if os.path.exists(db_path):
    #     os.remove(db_path)


@pytest.fixture
def s3_storage_model(faker) -> S3StorageOrm:
    return S3StorageOrm(
        name=faker.name(),
        url=f"test://{faker.bothify('???????.??/???????/?????????###')}",
        access_key=faker.address(),
        secret_key=faker.bothify('?#?#?#?#?#?#?#?#'),
    )


@pytest.fixture
def s3_backup_file_model(s3_storage_model, faker) -> BackupFileOrm:
    return BackupFileOrm(
        storage=s3_storage_model,
        path=faker.name,
        file_name=faker.address,
        file_size=random.randint(0, 1000),
        file_time=faker.date_between(start_date='-12m', end_date='today'),
        created_at=faker.date_between(start_date='-12m', end_date='today'),
    )


@pytest.fixture
def s3_storage_schema(s3_storage_model, faker) -> S3StorageDTO:
    return S3StorageDTO.model_validate(s3_storage_model, from_attributes=True)


@pytest.fixture
def created_s3_storage_dto(s3_storage_model) -> S3StorageRelDTO:
    with Session() as session:
        create_storage(session, s3_storage_model)
        session.commit()
        # return s3_storage_model
        return S3StorageRelDTO.model_validate(s3_storage_model, from_attributes=True)


@pytest.fixture
def created_s3_storage_orm(s3_storage_model) -> S3StorageOrm:
    with Session() as session:
        create_storage(session, s3_storage_model)
        session.commit()
        return s3_storage_model


# === Backup file
@pytest.fixture
def s3_backup_file_schema():
    backup_files = os.listdir(TEST_BACKUP_DIR)
    backup_file_name = random.choice(backup_files)
    backup_file_name_with_path = os.path.join(TEST_BACKUP_DIR, backup_file_name)
    file_size = os.path.getsize(backup_file_name_with_path)
    file_time = os.path.getmtime(backup_file_name_with_path)
    return S3BackupFileDTO(
        path=TEST_BACKUP_DIR,
        file_name=backup_file_name,
        file_size=file_size,
        file_time=file_time,
        created_at=None,
    )


@pytest.fixture
def created_backup_file(s3_backup_file_model):
    with Session() as session:
        create_storage(session, s3_backup_file_model.storage)
        create_backup_file(session, s3_backup_file_model)
