#!/usr/bin/env python3
"""
A script for use with the `ldb instantiate` command's `--apply` option. It
expects data from the TextOCR dataset, and demonstrates how to find
segmentations with a regex and generate an image from each segmentation's
bounding box.

For example:

    ldb instantiate --apply python3 path/to/textocr_crops.py '(?i)^(V?I{1,3}|I?[VX])$'

For information on TextOCR, see https://textvqa.org/textocr/dataset/
"""
import json
import os
import re
import sys
from typing import Sequence

from PIL import Image


def main(argv: Sequence[str], stdin_text: str) -> None:
    if len(argv) != 1:
        raise ValueError("expected exactly one argument, a regex pattern")
    source_dir, dest_dir = json.loads(stdin_text)
    generate_crops(source_dir, dest_dir, argv[0])


def generate_crops(source_dir: str, dest_dir: str, pattern: str) -> None:
    file_names = set(os.listdir(source_dir))
    pairs = {}
    for entry in file_names:
        if not entry.endswith(".json"):
            annot_path = os.path.splitext(entry)[0] + ".json"
            if annot_path in file_names:
                pairs[annot_path] = entry

    for annot_name, data_obj_name in pairs.items():
        create_roman_numeral_crops(
            os.path.join(source_dir, data_obj_name),
            os.path.join(source_dir, annot_name),
            dest_dir,
            pattern,
        )


def create_roman_numeral_crops(
    data_obj_path: str,
    annot_path: str,
    dest_dir: str,
    pattern: str,
) -> None:
    with open(annot_path, encoding="utf-8") as source_file:
        raw_annot = source_file.read()
    annot = json.loads(raw_annot)
    sub_annots = [
        a for a in annot["anns"] if re.search(pattern, a["utf8_string"])
    ]
    if sub_annots:
        data_obj_name = os.path.basename(data_obj_path)
        dest_base, ext = os.path.splitext(
            os.path.join(dest_dir, data_obj_name),
        )
        source_img = annot["img"]
        img = Image.open(data_obj_path)
        for i, sub_annot in enumerate(sub_annots, 1):
            new_path_base = f"{dest_base}-{i:03}"
            new_data_obj_path = f"{new_path_base}{ext}"
            new_annot_path = f"{new_path_base}.json"
            new_img = crop_bbox(img, sub_annot["bbox"])
            new_annot = {
                "source_img": source_img,
                "annotation": sub_annot,
            }
            new_raw_annot = json.dumps(new_annot, indent=2)
            with open(new_annot_path, "x", encoding="utf-8") as dest_file:
                dest_file.write(new_raw_annot)
            new_img.save(new_data_obj_path)


def crop_bbox(image: Image.Image, bbox: Sequence[float]) -> Image.Image:
    x, y, width, height = bbox
    return image.crop([x, y, x + width, y + height])  # type: ignore[arg-type]


if __name__ == "__main__":
    main(sys.argv[1:], sys.stdin.read())
