# Poetry Delta

A simple script that iterates through all the commits in a repository that contain modifications to `poetry.lock` or
`pyproject.toml` and generates a table that shows when a given dependency was added/removed/upgraded/downgraded.

For example in this repository:

```console
Processing /home/user/projects/gazwald/poetry-delta, on branch main
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Commit  ┃ Date                ┃ Author  ┃ Package        ┃ poetry.lock ┃ pyproject.toml ┃ State    ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ click          │ 8.1.7       │ ^8.1.7         │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ colorama       │ 0.4.6       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ gitdb          │ 4.0.11      │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ gitpython      │ 3.1.40      │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ iniconfig      │ 2.0.0       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ markdown-it-py │ 3.0.0       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ mdurl          │ 0.1.2       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ packaging      │ 23.2        │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pluggy         │ 1.3.0       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pygments       │ 2.16.1      │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pytest         │ 7.4.3       │ ^7.4.3         │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ rich           │ 13.6.0      │ ^13.6.0        │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ smmap          │ 5.0.1       │                │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ 054c36f │ 2023-11-17 11:35:13 │ gazwald │ rich           │ 13.7.0      │ ^13.6.0        │ UPGRADED │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ c48a58d │ 2023-11-19 15:01:24 │ gazwald │ pygments       │ 2.17.0      │                │ UPGRADED │
└─────────┴─────────────────────┴─────────┴────────────────┴─────────────┴────────────────┴──────────┘
```

## Usage

### Direct

```console
$ poetry run ./delta/run.py --path <path to your git repository>
```

By default it will look in the current directory, under the active branch, and show all changes for all packages.

```console
./delta/run.py --help
Usage: run.py [OPTIONS]

Options:
  --path TEXT     Path to the repository; default is cwd
  --branch TEXT   Branch to inspect
  --package TEXT  Package to filter on
  --rev TEXT      Rev, see `git rev-parse` for details.
  --help          Show this message and exit.
```

### Docker

By default the `run` script will mount either the current working directory or the first argument as `/mnt`.

```console
$ ./scripts/run <path to your git repository>
...
+++ Running poetry-delta +++
+++ Path: /home/user/projects/gazwald/poetry-delta +++
...
```

or, if you're running the container manually, you'll need to bind mount the path to the git repository to `/mnt` as
that is where the container expects the repository to be.

```console
$ docker run \
      --interactive \
      --rm \
      --tty \
      --volume "${REPO_PATH}:/mnt" \
      poetry-delta \
      "${@:2}" # Skip the first two elements
```

## TODO

- Actions
- Tests
- Colour blind mode(s)
