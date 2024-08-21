import asyncio

from common.BackupConfig import BackupConfig


async def backup():
    backup_config = BackupConfig()
    print(backup_config.backup_storages[0].items)
    for s3_storage in backup_config.backup_storages:
        print(f'Storage: {s3_storage.name} ({s3_storage.url}')
        for item in s3_storage.items:
            print(f'Item: {item.name} ({item.path} -> {item.bucket})')

if __name__ == '__main__':
    asyncio.run(backup())
