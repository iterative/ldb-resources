#!/usr/bin/env python3
import json
import os
import shutil
import sys
from typing import Dict, Sequence

from PIL import Image


def main(inp: Dict[str, str], argv: Sequence[str] = ()) -> None:
    data_object_path = inp["data_object"]
    annotation_path = inp["annotation"]
    output_dir = inp["output_dir"]
    transform_name = inp["transform_name"]

    if len(argv) > 1:
        print(
            "ERROR: No arguments expected",
            file=sys.stderr,
        )
        sys.exit(1)
    orig_image = Image.open(data_object_path)
    file_name_base, ext = os.path.splitext(os.path.basename(data_object_path))
    if ext.lstrip("."):
        fmt = None
    else:
        fmt = orig_image.format or "PNG"
        ext = ""

    new_image = orig_image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
    file_name_base = f"{file_name_base}--{transform_name}".replace(".", "-")
    obj_file_path = os.path.join(output_dir, f"{file_name_base}{ext}")
    annot_file_path = os.path.join(output_dir, f"{file_name_base}.json")
    new_image.save(obj_file_path, format=fmt)
    shutil.copy2(annotation_path, annot_file_path)


if __name__ == "__main__":
    main(json.loads(sys.stdin.read()), sys.argv)
