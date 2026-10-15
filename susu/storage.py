"""Validated JSON event storage for a single-process command-line tool."""

import json
import os
from pathlib import Path
import tempfile

from .errors import StateFileError, SusuError
from .group import SusuGroup


def restore(document):
    """Replay saved actions through the same validation used for new actions."""
    try:
        if not isinstance(document, dict) or set(document) != {"version", "weekly_contribution", "events"}:
            raise ValueError("Invalid document fields")
        if type(document["version"]) is not int or document["version"] != 1:
            raise ValueError("Unsupported state version")
        if not isinstance(document["events"], list):
            raise ValueError("Events must be a list")
        group = SusuGroup(document["weekly_contribution"])
        for event in document["events"]:
            if not isinstance(event, dict):
                raise ValueError("Invalid event")
            action = event.get("action")
            if action == "add" and set(event) == {"action", "member"}:
                group.add_member(event["member"])
            elif action == "pay" and set(event) == {"action", "member", "week", "amount"}:
                group.record_contribution(event["member"], event["week"], event["amount"])
            elif action == "close" and set(event) == {"action"}:
                if not group.close_week()["closed"]:
                    raise ValueError("Saved closure has unpaid contributions")
            else:
                raise ValueError("Invalid event fields or action")
        return group
    except (SusuError, ValueError, TypeError, KeyError) as exc:
        raise StateFileError(f"Invalid saved group: {exc}") from exc


def load(path):
    """Return the validated group and its document."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise StateFileError(f"Cannot read state file {path}: {exc}") from exc
    return restore(document), document


def save(path, document, *, create=False):
    """Validate before writing; replace existing state atomically."""
    restore(document)
    path = Path(path)
    temporary = None
    try:
        data = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if create:
            # Linking fails if a group already exists, preventing accidental overwrite.
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    except OSError as exc:
        raise StateFileError(f"Cannot save state file {path}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
