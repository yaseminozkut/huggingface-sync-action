from huggingface_hub import create_repo, whoami, HfApi, CommitOperationAdd, CommitOperationDelete
import os
import fnmatch


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y"}
    return False


def _is_ignored(path_in_repo: str, ignore_patterns: list[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    base = os.path.basename(path_in_repo)
    for pat in ignore_patterns:
        if fnmatch.fnmatch(path_in_repo, pat) or fnmatch.fnmatch(base, pat):
            return True
    return False


def _list_local_files(directory: str, ignore_patterns: list[str]) -> set[str]:
    """List all non-ignored files in a directory."""
    out: set[str] = set()
    directory = os.path.abspath(directory)

    for root, dirs, files in os.walk(directory):
        rel_root = os.path.relpath(root, directory)
        if rel_root == ".":
            rel_root = ""

        # Skip ignored directories early (e.g. ".github")
        kept_dirs = []
        for d in dirs:
            rel_dir = os.path.join(rel_root, d) if rel_root else d
            rel_dir_norm = rel_dir.replace(os.sep, "/")
            if not _is_ignored(rel_dir_norm, ignore_patterns):
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        for f in files:
            rel_file = os.path.join(rel_root, f) if rel_root else f
            rel_file_norm = rel_file.replace(os.sep, "/")
            if _is_ignored(rel_file_norm, ignore_patterns):
                continue
            out.add(rel_file_norm)

    return out


def main(
    repo_id: str,
    directory: str,
    token: str,
    repo_type: str = "space",
    space_sdk: str = "gradio",
    private=False,  # Fire will pass str, so let's normalize manually
):
    print("Syncing with Hugging Face Hub...")

    private = _to_bool(private)

    if "/" not in repo_id:
        username = whoami(token=token)["name"]
        repo_id = f"{username}/{repo_id}"

    print(f"\t- Repo ID: {repo_id}")
    print(f"\t- Directory: {directory}")
    print(f"\t- Private: {private}")

    url = create_repo(
        repo_id=repo_id,
        token=token,
        exist_ok=True,
        repo_type=repo_type,
        space_sdk=space_sdk if repo_type == "space" else None,
        private=private,
    )
    print(f"\t- Repo URL: {url}")

    ignore_patterns = ["*.git*", "*.github*"]

    api = HfApi(token=token)

    # List local files (filtered)
    local_files = _list_local_files(directory, ignore_patterns)
    print(f"\t- Local files found: {len(local_files)}")

    # List remote files (all files)
    remote_files_all = set(api.list_repo_files(repo_id=repo_id, repo_type=repo_type))
    print(f"\t- Remote files (before filtering): {len(remote_files_all)}")
    
    # Filter remote files to exclude ignored patterns
    remote_files = {p for p in remote_files_all if not _is_ignored(p, ignore_patterns)}
    print(f"\t- Remote files (after filtering): {len(remote_files)}")

    operations = []

    # Deletions: anything remote (not ignored) that no longer exists locally
    files_to_delete = remote_files - local_files
    if files_to_delete:
        print(f"\t- Files to delete: {len(files_to_delete)}")
        for path in sorted(files_to_delete):
            print(f"\t  - DELETE: {path}")
            operations.append(CommitOperationDelete(path_in_repo=path))

    # Add/Update: only files that are new or don't exist remotely
    files_to_add = local_files - remote_files
    if files_to_add:
        print(f"\t- Files to add: {len(files_to_add)}")
        for path in sorted(files_to_add):
            operations.append(
                CommitOperationAdd(
                    path_in_repo=path,
                    path_or_fileobj=os.path.join(directory, path),
                )
            )

    print(f"\t- Total operations: {len(operations)}")

    if not operations:
        print("\t- No changes detected, skipping commit")
        return

    api.create_commit(
        repo_id=repo_id,
        repo_type=repo_type,
        operations=operations,
        commit_message="Sync from GitHub via huggingface-sync-action",
    )
    print("\t- Repo synced")


if __name__ == "__main__":
    from fire import Fire
    Fire(main)