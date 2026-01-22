from huggingface_hub import create_repo, whoami, Repository
import os
import shutil


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y"}
    return False


def _clear_repo_except_git(path: str):
    for name in os.listdir(path):
        if name == ".git":
            continue
        full = os.path.join(path, name)
        if os.path.isdir(full):
            shutil.rmtree(full)
        else:
            os.remove(full)


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

    repo = Repository(
        local_dir="hf_repo",
        clone_from=repo_id,
        repo_type=repo_type,
        token=token,
    )

    _clear_repo_except_git("hf_repo")

    shutil.copytree(
        directory,
        "hf_repo",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("*.git*", "*.github*", "*README.md*"),
    )

    if repo.is_dirty():
        repo.push_to_hub(
            commit_message="Sync from GitHub via huggingface-sync-action"
        )
        print("\t- Repo synced")
    else:
        print("\t- No changes detected, skipping commit")


if __name__ == "__main__":
    from fire import Fire
    Fire(main)
