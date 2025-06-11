from pathlib import Path
from tracked_file_handler import TrackedFileHandler


def write_to_file(file_path: Path, content: str):
    file_path.write_text(content, encoding="utf-8")


def test_initialization_creates_file(tmp_path):
    tracked_file = tmp_path / "tracked.txt"
    assert not tracked_file.exists()

    handler = TrackedFileHandler(str(tracked_file))
    assert tracked_file.exists()
    assert handler.tracked_files == []
    assert handler.get_dangling_files() == []


def test_ignore_non_existing_files(tmp_path):
    tracked_file = tmp_path / "tracked.txt"
    non_existing_test_file = tmp_path / "a.txt"

    handler = TrackedFileHandler(str(tracked_file))
    assert handler.should_skip(str(non_existing_test_file))


def test_should_skip_and_upsert(tmp_path):
    tracked_file = tmp_path / "tracked.txt"
    test_file = tmp_path / "a.txt"
    write_to_file(test_file, "hello")

    handler = TrackedFileHandler(str(tracked_file))

    # Initially should not skip
    assert not handler.should_skip(str(test_file))

    # Upsert should update the tracked file list
    old_hash = handler.get_file_hash(str(test_file))
    result = handler.upsert_tracked_file(str(test_file))
    assert result is None
    assert handler.tracked_files == [f"{str(test_file)}@{old_hash}"]
    assert handler.should_skip(str(test_file))

    # Changing content should result in different hash and not skip
    write_to_file(test_file, "hello world")
    new_hash = handler.get_file_hash(str(test_file))
    assert old_hash != new_hash
    assert not handler.should_skip(str(test_file))


def test_delete_tracked_file(tmp_path):
    tracked_file = tmp_path / "tracked.txt"
    test_file = tmp_path / "b.txt"
    write_to_file(test_file, "some content")

    handler = TrackedFileHandler(str(tracked_file))
    handler.upsert_tracked_file(str(test_file))

    # Make sure the file is tracked
    assert handler.should_skip(str(test_file))

    # Now delete the tracked file
    old_hash = handler.get_file_hash(str(test_file))
    deleted_hash = handler.delete_tracked_file(str(test_file))
    assert deleted_hash == old_hash

    # Should not skip anymore
    assert not handler.should_skip(str(test_file))
    assert handler.tracked_files == []


def test_delete_while_upsert(tmp_path):
    """
    This is a simulation of what happens inside the ai_notes_indexer.py script.

    It combines other parts, but in general creates a tracked file,
    then changes some content in the file and checks that it correctly
    deletes the old tracked file entry and creates a new one.
    """

    tracked_file = tmp_path / "tracked.txt"
    test_file = tmp_path / "c.txt"
    write_to_file(test_file, "some content")

    handler = TrackedFileHandler(str(tracked_file))
    handler.upsert_tracked_file(str(test_file))
    initial_hash = handler.get_file_hash(str(test_file))

    assert handler.tracked_files == [f"{str(test_file)}@{initial_hash}"]
    assert handler.should_skip(str(test_file))

    write_to_file(test_file, "other content")
    assert not handler.should_skip(str(test_file))

    old_hash = handler.upsert_tracked_file(str(test_file))
    assert old_hash == initial_hash

    new_hash = handler.get_file_hash(str(test_file))
    assert handler.tracked_files == [f"{str(test_file)}@{new_hash}"]


def test_non_exisiting_file_should_be_dangling(tmp_path):
    tracked_file = tmp_path / "tracked.txt"
    dangling_file_content = "non_existing_test_file@df8b5ee26c20bd93d42e2e6254e7b780557bab3029f3f703cc05a97884fd5e7b"
    dangling_file_tracking = str(tmp_path / dangling_file_content)

    write_to_file(tracked_file, dangling_file_tracking)

    test_file = tmp_path / "a.txt"
    write_to_file(test_file, "some content")

    handler = TrackedFileHandler(str(tracked_file))
    handler.upsert_tracked_file(str(test_file))

    assert handler.tracked_files == [
        dangling_file_tracking,
        f"{str(test_file)}@{handler.get_file_hash(str(test_file))}",
    ]
    assert handler.get_dangling_files() == [dangling_file_tracking.split("@")[0]]


def test_hash_function_is_consistent(tmp_path):
    file = tmp_path / "file.txt"
    write_to_file(file, "test data")

    hash1 = TrackedFileHandler.get_file_hash(str(file))
    hash2 = TrackedFileHandler.get_file_hash(str(file))
    assert hash1 == hash2

    write_to_file(file, "different data")
    hash3 = TrackedFileHandler.get_file_hash(str(file))
    assert hash1 != hash3
