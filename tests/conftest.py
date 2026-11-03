import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from viridian_core.utils.blob_storage import (
    DEFAULT_BLOB_URL_PREFIX,
    DEFAULT_CONN_STR,
    build_blob_client,
    parse_blob_url,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# from common.progress_bar import ProgressManager
from viridian_core.utils import log_utils

env_path = Path.cwd() / ".env"

logging.getLogger("azure.core").setLevel(logging.WARNING)
log_utils.init()


@pytest.fixture(scope="session")
def data_resources():
    # Absolute path of the script
    script_path = os.path.abspath(__file__)
    test_dir = Path(script_path).parent
    data_resources_dir = os.path.join(test_dir, "data_resources")
    data_resources_dir += "/"
    yield data_resources_dir


@pytest.fixture(scope="session")
def simulate_blobs(data_resources):
    blobs = []
    blob_info = parse_blob_url(f"{DEFAULT_BLOB_URL_PREFIX}/xyz")
    service_client = BlobServiceClient.from_connection_string(DEFAULT_CONN_STR)
    container_client = service_client.get_container_client(blob_info.container_name)
    try:
        container_client.create_container()
    except ResourceExistsError:
        pass

    data_root = Path(data_resources)
    for file_path in data_root.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(data_root).as_posix()
        blob_url = f"{DEFAULT_BLOB_URL_PREFIX}/{relative_path}"
        blob_client = build_blob_client(
            blob_url=blob_url,
            connection_string=DEFAULT_CONN_STR,
        )
        blob_client.upload_blob(file_path.read_bytes(), overwrite=True)
        blobs.append(blob_client.blob_name)

    yield blobs


@pytest.fixture(scope="session")
def simulate_perf_blobs():
    blobs = []

    blob_info = parse_blob_url(f"{DEFAULT_BLOB_URL_PREFIX}/xyz")
    service_client = BlobServiceClient.from_connection_string(DEFAULT_CONN_STR)
    container_client = service_client.get_container_client(blob_info.container_name)
    try:
        container_client.create_container()
    except ResourceExistsError:
        pass
    finally:
        container_client.close()

    data_root = Path("/data/viridian/persistent/fixity/testdata")
    for file_path in data_root.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(data_root).as_posix()
        blob_url = f"{DEFAULT_BLOB_URL_PREFIX}/{relative_path}"
        blob_client = build_blob_client(
            blob_url=blob_url,
            connection_string=DEFAULT_CONN_STR,
        )

        if not blob_client.exists():
            blob_client.upload_blob(file_path.read_bytes(), overwrite=True)
        blobs.append(blob_client.blob_name)

    yield blobs
