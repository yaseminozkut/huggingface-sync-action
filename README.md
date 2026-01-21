# huggingface-sync-action

A GitHub action that syncs files from a GitHub repository to the Hugging Face Hub 🤗  

This fork fixes boolean input handling in GitHub composite actions and updates dependencies
to supported versions of `huggingface_hub` and `fire`.

## Usage

First, add a Hugging Face token with write access as a GitHub secret (e.g. `HF_TOKEN`).
Then use the action in your workflow:

```yaml
uses: alozowski/huggingface-sync-action@main
with:
  # The github repo you are syncing from (org/name). Required.
  github_repo_id: ''

  # The Hugging Face repo id you want to sync to (username/name). Required.
  huggingface_repo_id: ''

  # Hugging Face token with write access.
  hf_token: ${{ secrets.HF_TOKEN }}

  # The type of repo: model, dataset, or space.
  # Defaults to space.
  repo_type: 'space'

  # Whether to create the repo as private (only applies if it does not exist).
  private: false

  # Space SDK if repo_type is space: gradio, streamlit, or static.
  space_sdk: 'gradio'

  # Optional subdirectory to sync.
  # Defaults to syncing the entire repository.
  subdirectory: ''
```
