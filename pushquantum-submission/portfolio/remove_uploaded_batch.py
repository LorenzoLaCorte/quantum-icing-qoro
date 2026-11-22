"""Remove the 200- and 400-asset uploads identified in an Aqora upload log."""

import argparse
import re
from pathlib import Path, PurePosixPath


UPLOAD = re.compile(
    r"^Uploaded (pushquantum-2026-qoro/po_a(?:200|400)_[A-Za-z0-9_-]+\.(?:json|sol))$",
    re.MULTILINE,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="terminal log showing the successful uploads")
    parser.add_argument("--delete", action="store_true", help="delete the listed objects from Aqora")
    args = parser.parse_args()

    keys = sorted(set(UPLOAD.findall(args.log.read_text())))
    solutions = {PurePosixPath(key).stem for key in keys if key.endswith(".sol")}
    metadata = {PurePosixPath(key).stem for key in keys if key.endswith(".json")}
    if not solutions or solutions != metadata:
        parser.error("Expected complete .sol and .json pairs in the upload log")

    for key in keys:
        print(key)
    print(f"{len(solutions)} solutions, {len(keys)} Store objects")
    if not args.delete:
        return

    from aqora import Store

    store = Store()
    for key in keys:
        store.delete(key)
        print(f"Deleted {key}")


if __name__ == "__main__":
    main()
