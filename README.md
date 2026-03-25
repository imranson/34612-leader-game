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

## Testing Without the GUI

You can bypass the GUI and drive the engine directly in code. This is much faster for batch-testing different leader/follower combos:

```python
# ACCESS ENGINE DIRECTLY TO MASS TEST PARAMS
engine = Engine()
Leader.update_subclass_registry()
print([m for m in dir(engine) if not m.startswith('_')])

leader_chosen = Leader1
leader_object = leader_chosen(leader_chosen.__name__, engine)
follower_chosen = 'MK1'
```

Loop over leaders/followers to mass-test:

```python
for leader in [Leader1, SimpleLeader]:
    for follower in ['MK1', 'MK2', 'MK3']:
        # RUN THIS .connect AND .main_loop TO CONNECT THEN SIMULATE
        leader_chosen = leader
        leader_object = leader_chosen(leader_chosen.__name__, engine)
        follower_chosen = follower
        print(engine.connect(leader_object, leader_chosen.__name__, follower_chosen))
        print(engine.main_loop(101,130))
        print(leader_object.total_profit)
```