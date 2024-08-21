import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    DB_DSN: str = 'sqlite:///s3_backup.db'
    TEST_DB_DSN: str = 'sqlite:///test.db'
    if 'pytest' in sys.modules:
        CONFIG_FILE: str = os.path.join(ROOT_DIR, 'tests', 'test-config.json')
    else:
        CONFIG_FILE: str = os.path.join(ROOT_DIR, 'config.json')
    SECRET_KEY: str = '12345'
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
