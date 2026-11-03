from azure.core.exceptions import ResourceNotFoundError
from viridian_core.metadata import EntityInfo, FinalResultCode
from viridian_core.utils.blob_storage import DEFAULT_BLOB_URL_PREFIX, DEFAULT_CONN_STR
from viridian_core.utils.fixity_file import calculate_md5


def test_fixity_file_md5(simulate_blobs):
    for blob_name in simulate_blobs:
        blob_url = f"{DEFAULT_BLOB_URL_PREFIX}/{blob_name}"
        entity = EntityInfo(
            id=1,
            blob_url=blob_url,
        )
        ret = calculate_md5(entity)
        assert ret.state == FinalResultCode.FIXITY_FINISHED
        assert ret.checksum
        assert ret.blob_url == blob_url
        assert ret.error_desc is None


def test_fixity_file_md5_invalid_blob_url():
    entity = EntityInfo(
        id=1,
        blob_url="not-a-valid-url",
    )
    ret = calculate_md5(entity)
    assert ret.state == FinalResultCode.FILE_ENTRY_IN_DB_BUT_NOT_IN_FS
    assert "Invalid blob URL" in ret.error_desc


def test_fixity_file_md5_catches_storage_exception(monkeypatch):
    class _FailingBlobClient:
        blob_name = "missing.txt"

        def __init__(self):
            self.closed = False

        def exists(self):
            return False

        def get_blob_properties(self):
            raise ResourceNotFoundError(message="Blob not found")

        def close(self):
            self.closed = True

    failing_client = _FailingBlobClient()

    monkeypatch.setattr(
        "viridian_core.utils.fixity_file.build_blob_client",
        lambda **kwargs: failing_client,
    )

    entity = EntityInfo(
        id=1,
        blob_url="https://account.blob.core.windows.net/container/missing.txt",
    )
    ret = calculate_md5(entity)

    assert ret.state == FinalResultCode.FILE_ENTRY_IN_DB_BUT_NOT_IN_FS
    assert failing_client.closed is True
