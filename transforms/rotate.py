#!/usr/bin/env python3
import json
import os
import shutil
import sys
from math import cos, pi, sin
from typing import Dict, Sequence

from PIL import Image


def main(inp: Dict[str, str], argv: Sequence[str] = ()) -> None:
    data_object_path = inp["data_object"]
    annotation_path = inp["annotation"]
    output_dir = inp["output_dir"]
    transform_name = inp["transform_name"]

    transform_args = argv[1:] or ["90"]

    orig_image = Image.open(data_object_path)
    prefix, ext = os.path.splitext(os.path.basename(data_object_path))
    if ext.lstrip("."):
        fmt = None
    else:
        fmt = orig_image.format or "PNG"
        ext = ""
    for n in transform_args:
        new_image = rotate_and_crop(orig_image, int(n))
        file_name_base = f"{prefix}--{transform_name}--{n}".replace(
            ".",
            "-",
        )
        obj_file_path = os.path.join(output_dir, f"{file_name_base}{ext}")
        annot_file_path = os.path.join(output_dir, f"{file_name_base}.json")
        rgb_im = new_image.convert('RGB')
        rgb_im.save(obj_file_path, format=fmt)
        shutil.copy2(annotation_path, annot_file_path)


def rotate_and_crop(image, degrees):
    """
    Rotate the given image by `degrees`, and crop the resulting image
    to the largest rectangle with the original aspect ratio.
    """
    rotated_image = image.rotate(degrees, expand=True)
    w1, h1 = image.size
    w2, h2 = rotated_image.size
    r1 = w1 / h1
    r2 = w2 / h2
    angle = abs(degrees) * pi / 180
    if w1 < h1:
        total_height = w1 / r2
    else:
        total_height = h1
    h = abs(total_height / (r1 * abs(sin(angle)) + abs(cos(angle))))
    w = h * r1

    x1 = (w2 - w) / 2
    x2 = w2 - x1
    y1 = (h2 - h) / 2
    y2 = h2 - y1
    return rotated_image.crop([x1, y1, x2, y2])


if __name__ == "__main__":
    main(json.loads(sys.stdin.read()), sys.argv)
