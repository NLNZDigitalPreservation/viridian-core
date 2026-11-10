import pytest
from viridian_core.utils import blob_storage
from viridian_core.utils.blob_storage import (
    build_queue_client,
    extract_blob_name,
    parse_blob_url,
    parse_queue_url,
)


def test_extract_blob_name_production():
    blob_name = "path/to/file.txt"
    url = f"https://account.blob.core.windows.net/container/{blob_name}"
    extracted_name = blob_storage.extract_blob_name(url)
    assert extracted_name == blob_name


def test_extract_blob_name_production_with_leading_slash():
    blob_name = "/path/to/file.txt"
    url = f"https://account.blob.core.windows.net/container/{blob_name}"
    extracted_name = blob_storage.extract_blob_name(url)
    assert extracted_name == blob_name


def test_extract_blob_name_azurite():
    url = "http://127.0.0.1:10000/devstoreaccount1/container/path/to/file.txt"
    extracted_name = blob_storage.extract_blob_name(url)
    assert extracted_name == "path/to/file.txt"


def test_parse_blob_url_production():
    blob_name = "path/to/file.txt"
    url = f"https://account.blob.core.windows.net/container/{blob_name}"
    info = parse_blob_url(url)
    assert info.account_url == "https://account.blob.core.windows.net"
    assert info.container_name == "container"
    assert info.blob_name == blob_name


def test_parse_blob_url_production_with_leading_slash():
    blob_name = "/path/to/file.txt"
    url = f"https://account.blob.core.windows.net/container/{blob_name}"
    info = parse_blob_url(url)
    assert info.account_url == "https://account.blob.core.windows.net"
    assert info.container_name == "container"
    assert info.blob_name == blob_name


def test_parse_blob_url_azurite():
    url = "http://127.0.0.1:10000/devstoreaccount1/container/path/to/file.txt"
    info = parse_blob_url(url)
    assert info.account_url == "http://127.0.0.1:10000/devstoreaccount1"
    assert info.container_name == "container"
    assert info.blob_name == "path/to/file.txt"


def test_parse_blob_url_invalid_url():
    with pytest.raises(ValueError, match="Invalid blob URL"):
        parse_blob_url("not-a-valid-url")


def test_blob_name_is_malformed_for_unencoded_query_characters():
    malformed = blob_storage.BlobAccessArguments(
        account_url="https://account.blob.core.windows.net",
        account_name="account",
        container_name="container",
        _blob_name="folder/file?name.txt",
        index_location="folder/file?name.txt",
    )
    assert malformed.blob_name == "folder/file?name.txt"
    assert malformed.is_blob_name_malformed() is True

    malformed_2 = blob_storage.BlobAccessArguments(
        account_url="https://account.blob.core.windows.net",
        account_name="account",
        container_name="container",
        _blob_name="folder/file&name.txt",
        index_location="folder/file&name.txt",
    )
    assert malformed_2.blob_name == "folder/file&name.txt"
    assert malformed_2.is_blob_name_malformed() is True

    valid = blob_storage.BlobAccessArguments(
        account_url="https://account.blob.core.windows.net",
        account_name="account",
        container_name="container",
        _blob_name="folder/file%3Fname.txt",
        index_location="folder/file%3Fname.txt",
    )
    assert valid.blob_name == "folder/file?name.txt"
    assert valid.is_blob_name_malformed() is False


def test_parse_queue_url_production():
    url = "https://account.queue.core.windows.net/my-queue"
    info = parse_queue_url(url)
    assert info.account_url == "https://account.queue.core.windows.net"
    assert info.queue_name == "my-queue"


def test_parse_queue_url_azurite():
    url = "http://127.0.0.1:10001/devstoreaccount1/my-queue"
    info = parse_queue_url(url)
    assert info.account_url == "http://127.0.0.1:10001/devstoreaccount1"
    assert info.queue_name == "my-queue"


def test_build_queue_client_with_connection_string_verify_ssl_true(monkeypatch):
    captured = {}

    class _FakeQueueClient:
        def create_queue(self):
            return None

    def fake_from_connection_string(**kwargs):
        captured.update(kwargs)
        return _FakeQueueClient()

    monkeypatch.setattr(
        blob_storage.QueueClient,
        "from_connection_string",
        staticmethod(fake_from_connection_string),
    )

    queue_client = build_queue_client(
        queue_url="https://account.queue.core.windows.net/my-queue",
        connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;",
        verify_ssl=True,
    )

    assert queue_client is not None
    assert captured["queue_name"] == "my-queue"
    assert captured["connection_verify"] is True


def test_build_queue_client_with_connection_string_verify_ssl_and_cert_path(
    monkeypatch, tmp_path
):
    captured = {}

    class _FakeQueueClient:
        def create_queue(self):
            return None

    def fake_from_connection_string(**kwargs):
        captured.update(kwargs)
        return _FakeQueueClient()

    monkeypatch.setattr(
        blob_storage.QueueClient,
        "from_connection_string",
        staticmethod(fake_from_connection_string),
    )

    cert_dir = tmp_path / "fixity"
    cert_dir.mkdir()
    (cert_dir / "fixity.cer").write_text("-----BEGIN CERTIFICATE-----\nMIIB\n")
    (cert_dir / "fixity.key").write_text("-----BEGIN PRIVATE KEY-----\nMIIE\n")

    queue_client = build_queue_client(
        queue_url="https://account.queue.core.windows.net/my-queue",
        connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;",
        verify_ssl=True,
        ssl_cert_path=str(cert_dir),
    )

    assert queue_client is not None
    assert captured["connection_verify"] is True
    assert captured["connection_cert"] == (
        str(cert_dir / "fixity.cer"),
        str(cert_dir / "fixity.key"),
    )


def test_guess_index_location():
    assert (
        blob_storage.guess_index_location("2026/09/V1-FL1156.jpg")
        == "2026/09/V1-FL1156.jpg"
    )

    assert (
        blob_storage.guess_index_location("2026/09/V1-FL1156_jpg")
        == "2026/09/V1-FL1156_jpg"
    )

    # Invalid pattern, should return the original blob name
    assert (
        blob_storage.guess_index_location(
            "exlibris1/permanent_storage/file_01/2026/09/V1-FL1156.jpg"
        )
        == "exlibris1/permanent_storage/file_01/2026/09/V1-FL1156.jpg"
    )

    assert (
        blob_storage.guess_index_location(
            "/exlibris1/permanent_storage/md_01/2008/10/24/md_1/V1-1046.xml"
        )
        == "2008/10/24/md_1/V1-1046.xml"
    )

    assert (
        blob_storage.guess_index_location(
            "/exlibris1/permanent_storage/md_01/2008/10/24/md_1/master/V1-1046.xml"
        )
        == "2008/10/24/md_1/master/V1-1046.xml"
    )

    assert (
        blob_storage.guess_index_location("2026/09/03/V1-FL1156.jpg")
        == "2026/09/03/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location("/2026/09/03/V1-FL1156.jpg")
        == "2026/09/03/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location(
            "exlibris1/permanent_storage/file_01/2026/09/03/V1-FL1156.jpg"
        )
        == "2026/09/03/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location(
            "/exlibris1/permanent_storage/file_01/2026/09/03/V1-FL1156.jpg"
        )
        == "2026/09/03/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location("2026/09/03/file_01/V1-FL1156.jpg")
        == "2026/09/03/file_01/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location("/2026/09/03/file_01/V1-FL1156.jpg")
        == "2026/09/03/file_01/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location(
            "exlibris1/permanent_storage/2026/09/03/file_01/V1-FL1156.jpg"
        )
        == "2026/09/03/file_01/V1-FL1156.jpg"
    )
    assert (
        blob_storage.guess_index_location(
            "/exlibris1/permanent_storage/2026/09/03/file_01/V1-FL1156.jpg"
        )
        == "2026/09/03/file_01/V1-FL1156.jpg"
    )


def test_url_with_blob_prefix_01():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01/exlibris1/permanent_storage/file_01/2026/09/03/V1-FL1156.jpg"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert blob_info.index_location == "/2026/09/03/V1-FL1156.jpg"
    assert blob_info.blob_prefix == "exlibris1/permanent_storage/file_01"


def test_url_with_blob_prefix_02():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01/exlibris1/file_01/2026/09/03/V1-FL1156.?jpg"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert blob_info.index_location == "/2026/09/03/V1-FL1156.?jpg"
    assert blob_info.blob_prefix == "exlibris1/file_01"


def test_url_with_blob_prefix_03():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01/exlibris1/sip_01/2026/09/03/V1-FL1156.jpg?a=123&b=456"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert (
        blob_info.blob_name == "exlibris1/sip_01/2026/09/03/V1-FL1156.jpg?a=123&b=456"
    )
    assert blob_info.index_location == "/2026/09/03/V1-FL1156.jpg?a=123&b=456"
    assert blob_info.blob_prefix == "exlibris1/sip_01"


def test_url_with_blob_prefix_04():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01/exlibris1/permanent_storage/file_01/2026/08/25/file_1/V4-IE1033.xml"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert (
        blob_info.blob_name
        == "exlibris1/permanent_storage/file_01/2026/08/25/file_1/V4-IE1033.xml"
    )
    assert blob_info.index_location == "/2026/08/25/file_1/V4-IE1033.xml"
    assert blob_info.blob_prefix == "exlibris1/permanent_storage/file_01"


def test_url_without_blob_prefix_01():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01/2026/03/08/V1-FL1156.jpg"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert blob_info.blob_name == "2026/03/08/V1-FL1156.jpg"
    assert blob_info.index_location == "/2026/03/08/V1-FL1156.jpg"
    assert blob_info.is_empty_blob_prefix()


def test_url_without_blob_prefix_02():
    blob_url = "https://stanlnznblobdevrosi01.blob.core.windows.net/stct-permrp-01//2026/03/08/V1-FL1156.jpg"
    blob_info = parse_blob_url(blob_url)
    assert (
        blob_info.account_url == "https://stanlnznblobdevrosi01.blob.core.windows.net"
    )
    assert blob_info.container_name == "stct-permrp-01"
    assert blob_info.blob_name == "/2026/03/08/V1-FL1156.jpg"
    assert blob_info.index_location == "/2026/03/08/V1-FL1156.jpg"
    assert blob_info.is_empty_blob_prefix()
