from azure.core.exceptions import ResourceNotFoundError
from viridian_core.metadata import EntityInfo, FinalResultCode
from viridian_core.utils.blob_storage import DEFAULT_BLOB_URL_PREFIX
from viridian_core.utils.fixity_mets_xml import parse_mets_xml


def test_parse_mets_xml_success(simulate_blobs):
    """
    Test parsing a METS XML file successfully.
    """
    for blob in simulate_blobs:
        if not blob.endswith("ie.xml"):
            continue

        entity = EntityInfo(
            id=1,
            blob_url=f"{DEFAULT_BLOB_URL_PREFIX}/{blob}",
        )

        ret = parse_mets_xml(entity)
        assert ret.state == FinalResultCode.FIXITY_FINISHED
        assert ret.coll is not None

        for item in ret.coll:
            assert "amd_id" in item
            assert "checksum_type" in item
            assert "checksum" in item
            assert "blob_name" in item
            assert item["amd_id"] is not None
            assert item["checksum_type"] is not None
            assert item["checksum"] is not None
            assert item["blob_name"] is not None


def test_parse_mets_xml_missing_blob(monkeypatch):
    """
    Test parsing a METS XML file when the corresponding blob is missing.
    """

    class _MissingBlobClient:
        blob_name = "missing.xml"

        def __init__(self):
            self.closed = False

        def exists(self):
            return False

        def download_blob(self):
            raise ResourceNotFoundError(message="Blob not found")

        def close(self):
            self.closed = True

    missing_client = _MissingBlobClient()

    monkeypatch.setattr(
        "viridian_core.utils.fixity_mets_xml.build_blob_client",
        lambda **kwargs: missing_client,
    )

    entity = EntityInfo(
        id=1,
        blob_url="https://account.blob.core.windows.net/container/missing.xml",
    )

    ret = parse_mets_xml(entity)

    assert ret.state == FinalResultCode.FILE_ENTRY_IN_DB_BUT_NOT_IN_FS
    assert missing_client.closed is True
