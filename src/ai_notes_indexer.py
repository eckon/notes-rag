import argparse
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from pinecone import AwsRegion, CloudProvider, EmbedModel, IndexEmbed, Pinecone

from config import (
    CYAN,
    GREEN,
    GREY,
    IN_CI,
    INDEX_NAME,
    INDEX_NAMESPACE,
    MAGENTA,
    PINECONE_API_KEY,
    RED,
    RESET,
    TRACKED_FILE,
    YELLOW,
)
from markdown_chunker import chunk_markdown_by_heading, chunk_markdown_by_list
from tracked_file_handler import TrackedFileHandler


class NotesIndexer:
    """
    This class is used to index my notes by creating vectors in a vector database.
    """

    def __init__(self, notes_path: str, testing=False):
        # to allow running in both the rag and the notes repo, keep track of the root of both
        self.rag_repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()

        # move to the root of the git repo which was passed, even if moved to a subfolder (notes repo)
        # via git we will go to the root of it
        os.chdir(notes_path)
        self.notes_repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
        os.chdir(self.notes_repo_root)

        testing_name = "testing-index"
        self.index_name = INDEX_NAME if not testing else testing_name
        self.tracked_files_path = (
            f"{self.rag_repo_root}/{TRACKED_FILE}"
            if not testing
            else f"{self.rag_repo_root}/{testing_name}.txt"
        )

        if not IN_CI:
            self.confirm_execution()

        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        if not self.pc.has_index(self.index_name):
            print(
                f"\n{MAGENTA}Creating{RESET} index{RESET} - {CYAN}{self.index_name}{RESET}"
            )
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud=CloudProvider.AWS,
                region=AwsRegion.US_EAST_1,
                embed=IndexEmbed(
                    model=EmbedModel.Multilingual_E5_Large,
                    metric="cosine",
                    field_map={"text": "text"},
                ),
            )
            time.sleep(1)

        self.index = self.pc.Index(self.index_name)
        self.f_handler = TrackedFileHandler(self.tracked_files_path)

    def process_markdown_file(self, file_path: Path) -> None:
        # hash will be used to delete old vectors when notes are updated
        file_hash = self.f_handler.get_file_hash(str(file_path))

        with open(file_path, "r", encoding="utf-8") as file:
            markdown = file.read()

        print(f"{GREY}Splitting markdown by sections{RESET}")
        chunked_markdown = chunk_markdown_by_heading(markdown)

        metadata = {
            "filename": file_path.name,
            "path": str(file_path.parent),
            "type": "section",
            "hash": file_hash,
        }

        records = self.create_records(chunked_markdown, metadata)

        print(f"{GREY}Splitting markdown by lists{RESET}")
        chunked_lists = chunk_markdown_by_list(markdown)

        # overwrite the metadata type to list, as we want to upload both sections and lists
        metadata["type"] = "list"
        records.extend(self.create_records(chunked_lists, metadata))

        if records:
            print(f"{YELLOW}Uploading {GREEN}{len(records)}{RESET} records")
            self.index.upsert_records(namespace=INDEX_NAMESPACE, records=records)

    def create_records(
        self, chunks: list[str], metadata_base: dict[str, str]
    ) -> list[dict]:
        records = []
        for i, chunk in enumerate(chunks):
            print(
                f"{YELLOW}Create {GREEN}{i + 1}/{len(chunks)}{RESET} records", end="\r"
            )

            record = {
                "id": str(uuid.uuid4()),
                "text": chunk,
                **metadata_base,
            }

            records.append(record)

        # go to next line, to not overwrite the creating records line
        print()

        return records

    def run(self) -> None:
        print(f"\n{GREEN}Starting creation/uploading of new vectors for notes{RESET}\n")

        # use git ls-files to get all files in the repo, to avoid ignored files like node_modules etc.
        tracked_files = subprocess.check_output(
            ["git", "ls-files"],
            text=True,
        ).splitlines()

        files = [Path(f) for f in tracked_files if f.endswith(".md")]

        for i, file_path in enumerate(files):
            if self.f_handler.should_skip(str(file_path)):
                # skip because the file and its content has already been processed
                print(f"{GREY}Skipping: {file_path}{RESET}")
                continue

            # add a new line for visual separation and overview of progression
            print(
                f"\n{MAGENTA}Working{RESET} on file {GREEN}{i + 1}/{len(files)}{RESET} - {CYAN}{file_path}{RESET}"
            )
            self.process_markdown_file(file_path)

            # keep track of the file and its hash to skip it on future runs
            print(
                f"{GREEN}Finished{RESET} work on file and {GREEN}Save{RESET} current tracking locally"
            )
            old_tracked_file = self.f_handler.upsert_tracked_file(str(file_path))
            if old_tracked_file:
                print(f"{RED}Purge{RESET} old index in db")
                self.index.delete(
                    namespace=INDEX_NAMESPACE, filter={"hash": old_tracked_file}
                )

            # more visual separation (in case of many skipped files)
            print()

        # check if we have references to dangling files that need to be deleted
        dangling_files = self.f_handler.get_dangling_files()
        if dangling_files:
            print(
                f"\n{MAGENTA}Found{RESET} Dangling files, start {RED}Deleting{RESET} them"
            )
            for file in dangling_files:
                old_tracked_file = self.f_handler.delete_tracked_file(file)
                print(f"{RED}Deleting: {CYAN}{file}{RESET}")
                if old_tracked_file:
                    print(f"{RED}Purge{RESET} old index in db")
                    self.index.delete(
                        namespace=INDEX_NAMESPACE, filter={"hash": old_tracked_file}
                    )
                else:
                    print(
                        f"{RED}WARNING:{RESET} Deleted {CYAN}{file}{RESET} but {YELLOW}Ignored{RESET} index in db"
                    )

        # check tracked files and delete non existing files
        print(f"\n{GREEN}Finished script{RESET}")

    def confirm_execution(self) -> None:
        answer = (
            input(
                f"""
This action might {RED}break{RESET} the current connected setup, check if you have the latest changes of this repo:
DB INDEX:      {MAGENTA}{self.index_name}{RESET}
NOTES REPO:    {CYAN}{self.notes_repo_root}{RESET}
RAG REPO:      {CYAN}{self.rag_repo_root}{RESET}
TRACKED FILES: {GREY}{self.tracked_files_path}{RESET}
Are you sure?{YELLOW} (y/N): {RESET}"""
            )
            .strip()
            .lower()
        )

        if answer not in {"yes", "y"}:
            print(f"{YELLOW}Operation cancelled{RESET}")
            exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prod", action="store_true", help="Run in production mode")
    parser.add_argument(
        "--root",
        type=str,
        help="Path to the root of a git repo",
        default=os.path.expanduser("~/Documents/notes"),
    )

    try:
        args = parser.parse_args()
        NotesIndexer(testing=not args.prod, notes_path=args.root).run()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Operation cancelled{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
