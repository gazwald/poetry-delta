# Poetry Delta

Iterates through commits in a repository and generates a table showing 
which libraries were added/removed and when their versions changed.

For example in this repo:

```console
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Commit  ┃ Date                ┃ Author  ┃ Package        ┃ poetry.lock ┃ State    ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ click          │ 8.1.7       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ colorama       │ 0.4.6       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ gitdb          │ 4.0.11      │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ gitpython      │ 3.1.40      │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ iniconfig      │ 2.0.0       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ markdown-it-py │ 3.0.0       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ mdurl          │ 0.1.2       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ packaging      │ 23.2        │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pluggy         │ 1.3.0       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pygments       │ 2.16.1      │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ pytest         │ 7.4.3       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ rich           │ 13.6.0      │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 94197c3 │ 2023-11-13 08:51:38 │ gazwald │ smmap          │ 5.0.1       │ ADDED    │
├─────────┼─────────────────────┼─────────┼────────────────┼─────────────┼──────────┤
│ 054c36f │ 2023-11-17 11:35:13 │ gazwald │ rich           │ 13.7.0      │ UPGRADED │
└─────────┴─────────────────────┴─────────┴────────────────┴─────────────┴──────────┘
```

## Usage

```console
$ ./delta/run.py
```

By default it will look in the current directory, under the active branch, and show all changes for all packages.

...


## TODO

- Add pyproject information back in (don't do a comparison though)
- Docker
- General cleanup
