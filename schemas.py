from datetime import datetime
from typing import Any, List
import os
from pydantic import BaseModel, Field, model_validator

# =================================================================
#
# Data Transfer Objects
#
# =================================================================

# For files/folders from JSON config:
class BackupStorage(BaseModel):
    """Server config"""
    name: str = Field()
    url: str = Field()
    access_key: str = Field()
    secret_key: str = Field()
    items: List["BackupItem"]

class BackupItem(BaseModel):
    """For config json items (files or folders)"""
    name: str = Field()
    bucket: str = Field()
    path: str = Field()
    include: list[str] | None = None
    exclude: list[str] | None = None
    is_file: bool = False
    is_directory: bool = False
    items: List['BackupItem'] = []

    @model_validator(mode='before')
    @classmethod
    def validate_item_exists(cls, data: Any):
        if os.path.isfile(data['path']):
            data['is_file'] = True
        elif os.path.isdir(data['path']):
            data['is_directory'] = True
        else:
            print(f'Invalid path {data["path"]}')
            raise ValueError(f'Invalid path {data["path"]}')
        return data


# For DB models:
class S3StorageAddDTO(BaseModel):
    name: str = Field()
    url: str = Field()
    access_key: str = Field()
    secret_key: str = Field()


class S3StorageDTO(S3StorageAddDTO):
    """For json and db storages"""
    id: int | None = None


class S3BackupFileAddDTO(BaseModel):
    path: str = Field()
    file_name: str = Field()
    file_size: int = Field()
    file_time: datetime = Field()


class S3BackupFileDTO(S3BackupFileAddDTO):
    """For db backup file (model)
    id: int | None
    storage_id: int
    path: str
    file_name: str
    file_size: int
    file_time: datetime
    created_at: datetime
    """
    id: int | None = None
    created_at: datetime | None = None
    storage_id: int | None = None


# For DB Models with relations:
class S3BackupFileRelDTO(S3BackupFileDTO):
    storage: S3StorageDTO

class S3StorageRelDTO(S3StorageDTO):
    items: list['S3BackupFileDTO'] = []
