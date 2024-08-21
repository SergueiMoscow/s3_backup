from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, backref, Mapped, mapped_column, relationship
from typing import Annotated


STRING_255 = 255
STRING_32 = 32

Base = declarative_base()

LAZY_TYPE = 'select'

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]

class S3StorageOrm(Base):
    __tablename__ = 's3_storages'
    id: Mapped[intpk]
    name = Column(String(STRING_32), nullable=False)
    url = Column(String(STRING_255), nullable=False)
    access_key = Column(String(STRING_255), nullable=False)
    secret_key = Column(String(STRING_255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    files: Mapped[list['BackupFileOrm']] = relationship(
        back_populates='storage',
    )


class BackupFileOrm(Base):
    __tablename__ = 'backup_file'
    id: Mapped[intpk]
    storage_id = mapped_column(ForeignKey('s3_storages.id', ondelete='CASCADE'), nullable=False)
    path = Column(String(STRING_255), nullable=False)
    file_name = Column(String(STRING_255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

    storage: Mapped['S3StorageOrm'] = relationship(back_populates='files')
