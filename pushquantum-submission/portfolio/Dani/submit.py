"""Upload the portfolio solution/JSON pairs beside this script to Aqora storage."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="upload the listed files to your Aqora store")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    solutions = sorted(folder.glob("*.sol"))
    if not solutions:
        parser.error(f"No .sol files found in {folder}")

    files = []
    for solution in solutions:
        metadata_file = solution.with_suffix(".json")
        if not metadata_file.exists():
            parser.error(f"Missing metadata: {metadata_file.name}")
        metadata = json.loads(metadata_file.read_text())
        qubits = metadata.get("qubits")
        if type(qubits) is not int or qubits < 0 or not isinstance(metadata.get("method"), str):
            parser.error(f"Expected nonnegative integer qubits and string method in {metadata_file.name}")
        files.extend([metadata_file, solution])
        print(f"{solution.stem}: {qubits} qubits")

    print(f"{len(solutions)} solutions, {len(files)} files")
    if not args.upload:
        print("Preview complete. Run with --upload to copy these files to your Aqora store.")
        return

    try:
        from aqora import Store
    except ImportError:
        parser.error("Install aqora in this Python environment with: python -m pip install aqora")
    store = Store()
    for path in files:
        key = f"pushquantum-2026-qoro/{path.name}"
        content_type = "application/json" if path.suffix == ".json" else "text/plain"
        store.put(key, path.read_bytes(), content_type=content_type)
        print(f"Uploaded {key}")
    print("Open https://aqora.io/qoro/pushquantum-2026-leaderboard, sign in, and press Submit.")


if __name__ == "__main__":
    main()
