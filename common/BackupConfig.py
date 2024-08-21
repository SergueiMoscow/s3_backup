import json

from common.settings import settings
from schemas import BackupStorage


class BackupConfig:
    def __init__(self):
        settings_dict: dict = self.get_settings()
        self.backup_storages: list[BackupStorage] = []
        for s3_storage in settings_dict['s3_storages']:
            validated_backup_storage = BackupStorage.model_validate(s3_storage)
            self.backup_storages.append(validated_backup_storage)

    def get_settings(self) -> dict:
        with open(settings.CONFIG_FILE) as f:
            settings_dict = json.load(f)
        return settings_dict
