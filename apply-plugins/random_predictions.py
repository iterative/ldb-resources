#!/usr/bin/env python3
import json
import os
import random
import shutil
import sys
from typing import Sequence


def main(argv: Sequence[str] = ()) -> None:
    source_dir = argv[0]
    dest_dir = argv[1]
    for entry in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, entry)
        dest_file_path = os.path.join(dest_dir, entry)
        if entry.endswith(".json"):
            pred = random.random()
            write_prediction(source_file_path, dest_file_path, pred)
        else:
            shutil.move(source_file_path, dest_file_path)


def write_prediction(
    source_file_path: str,
    dest_file_path: str,
    prediction: float,
) -> None:
    with open(source_file_path, encoding="utf-8") as source_file:
        raw_annot = source_file.read()
    annot = json.loads(raw_annot)
    annot["prediction"] = prediction
    new_raw_annot = json.dumps(annot, indent=2)
    with open(dest_file_path, "x", encoding="utf-8") as dest_file:
        dest_file.write(new_raw_annot)


if __name__ == "__main__":
    main(json.loads(sys.stdin.read()))
