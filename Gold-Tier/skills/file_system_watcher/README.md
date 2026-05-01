# File System Watcher Skill

**Agent entry point for monitoring folders for new files and creating action tasks.**

## Quick Use

```python
from skills.file_system_watcher.skill import scan_watch_folder

result = scan_watch_folder(watch_folder="C:/Users/me/Downloads/WorkDrop")
print(f"New files: {result['count']}")
```

## Available Functions

| Function | Purpose |
|---|---|
| `scan_watch_folder(watch_folder, move_processed)` | Scan folder, create action files, move files |
| `list_unprocessed_files(watch_folder)` | List unprocessed files without processing them |

## Schema

See `schema.json` for the agent tool definition.

## Architecture

```
Agent → skill.py (entry point) → service.py → file system scan → Needs_Action/*.md + Inbox/
```

## What Changed From Old System

| Old | New |
|---|---|
| `scripts/filesystem_watcher.py` standalone daemon with infinite polling loop | `service.py` with callable `scan_folder()` method |
| `FileSystemWatcher.run()` blocked forever | Agent calls `scan_watch_folder()` on demand |
| Hash tracking mixed in with BaseWatcher inheritance | Self-contained service with hash management |
| No agent tool definition | `schema.json` defines parameters for LLM selection |

## Prerequisites

- AI Employee Vault with Needs_Action/, Inbox/, Logs/ folders
- A folder to monitor (must exist or will be created)
