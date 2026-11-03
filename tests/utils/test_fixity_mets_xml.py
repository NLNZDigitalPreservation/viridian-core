from azure.core.exceptions import ResourceNotFoundError
from viridian_core.metadata import EntityInfo, FinalResultCode
from viridian_core.utils.fixity_mets_xml import parse_mets_xml


def test_parse_mets_xml_missing_blob(monkeypatch):
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
