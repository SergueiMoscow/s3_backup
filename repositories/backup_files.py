from sqlalchemy import update, and_, select
from sqlalchemy.orm import Session

from db.models import BackupFileOrm


def create_backup_file(session: Session, backup_file: BackupFileOrm) -> BackupFileOrm:
    session.add(backup_file)
    return backup_file


def update_backup_file(session: Session, backup_file_id: int, update_data: dict) -> BackupFileOrm:
    backup_file = session.scalar(select(BackupFileOrm).where(BackupFileOrm.id == backup_file_id))
    if not backup_file:
        return None
    for key, value in update_data.items():
        setattr(backup_file, key, value)
    session.commit()
    return backup_file

def get_backup_file_by_id(session: Session, backup_file_id: int) -> BackupFileOrm | None:
    return session.query(BackupFileOrm).filter(BackupFileOrm.id == backup_file_id).one_or_none()


def get_backup_file_by_path_and_name(session: Session, path: str, name: str) -> BackupFileOrm | None:
    return session.query(BackupFileOrm).filter(
        and_(
            BackupFileOrm.path == path,
            BackupFileOrm.name == name,
        )
    ).one_or_none()
