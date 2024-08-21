import copy

from db.engine import Session
from db.models import S3StorageOrm, BackupFileOrm
from repositories.backup_files import create_backup_file, get_backup_file_by_id, update_backup_file
from repositories.s3_storages import create_storage, update_storage, get_storage_by_id, delete_storage
from schemas import S3StorageDTO, BackupItem, S3BackupFileDTO, S3BackupFileRelDTO
from services.Encryption import encryption_service
from services.s3_storages import decrypt_storage

fields_to_encrypt = ('url', 'access_key', 'secret_key')



def create_s3_backup_file_service(backup_file: S3BackupFileDTO, storage: S3StorageOrm) -> S3BackupFileDTO:
    backup_file_model = BackupFileOrm(storage=storage, **S3BackupFileDTO.model_dump(backup_file))
    with Session() as session:
        create_backup_file(session, backup_file_model)
        session.commit()
        result = S3BackupFileDTO.model_validate(backup_file_model, from_attributes=True)
    return result


def update_s3_backup_file_service(backup_file_id: int, s3_backup_file_updated: S3BackupFileDTO) -> S3BackupFileDTO:
    with Session() as session:
        s3_backup_file = get_backup_file_by_id(session, backup_file_id)
        if s3_backup_file is None:
            raise ValueError("s3_backup_file_model not found with id: %s" % backup_file_id)
        return update_backup_file(session, backup_file_id, s3_backup_file_updated.model_dump())


def get_s3_storage_by_id_service(s3_storage_id: int) -> S3StorageOrm | None:
    with Session() as session:
        s3_storage = get_storage_by_id(session, s3_storage_id)
        decrypted_s3_storage = decrypt_storage(s3_storage)
        return decrypted_s3_storage


def delete_storage_service(s3_storage_id: int) -> None:
    with Session() as session:
        s3_storage = get_storage_by_id(session, s3_storage_id)
        delete_storage(s3_storage)
