import pytest

from services.backup import backup

@pytest.mark.asyncio
async def test_backup():
    await backup()
