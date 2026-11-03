from viridian_core.utils.blob_storage import guess_entity_info


def test_guess_entity_info():
    def _guess_entity_info(blob_prefix):
        blob_name = f"{blob_prefix}/V1-FL12345.txt"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 1
        assert entity_info.storage_entity_type == "FILE"
        assert entity_info.stored_entity_id == "FL12345"

        blob_name = f"{blob_prefix}/V1-FL679300.gee form letter"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 1
        assert entity_info.storage_entity_type == "FILE"
        assert entity_info.stored_entity_id == "FL679300"

        blob_name = f"{blob_prefix}/2008/12/11/file_1/V1-FL876654.a25+"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 1
        assert entity_info.storage_entity_type == "FILE"
        assert entity_info.stored_entity_id == "FL876654"

        blob_name = f"{blob_prefix}/V2-IE67890.data"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 2
        assert entity_info.storage_entity_type == "IE"
        assert entity_info.stored_entity_id == "IE67890"

        blob_name = f"{blob_prefix}/V2-IE67890"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 2
        assert entity_info.storage_entity_type == "IE"
        assert entity_info.stored_entity_id == "IE67890"

        blob_name = f"{blob_prefix}/V2-IE67890.jpg.bak"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is not None
        assert entity_info.version == 2
        assert entity_info.storage_entity_type == "IE"
        assert entity_info.stored_entity_id == "IE67890"

        blob_name = f"{blob_prefix}/invalid_blob_name.txt"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is None

        blob_name = f"{blob_prefix}/2-IE67890.data"
        entity_info = guess_entity_info(blob_name)
        assert entity_info is None

    for blob_prefix in [
        "",
        "/",
        "prefix1",
        "prefix2/subdir",
        "/prefix1",
        "/prefix2/subdir",
    ]:
        _guess_entity_info(blob_prefix)
