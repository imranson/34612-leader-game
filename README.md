# COMP34612 Games Coursework

## CSF3 usage tips IMPORTANT
if below:
```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```
then run
```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## Setup

1. Place downloads in the `downloads/` folder (gitignored).

**Do not push large files (datasets, models, etc.) to the repo.**

## Workflow

- **Create a branch for everything.** Do not commit directly to `main`.
- **Try not to merge to `main` unless everyone is around.** Coordinate merges so the whole team can review together.

## Code

- **Use Python scripts (`.py`) rather than notebooks for development (unless u don't have CSF access).** Scripts are easier to review, merge, and version-control.
- Notebooks for final submission.
