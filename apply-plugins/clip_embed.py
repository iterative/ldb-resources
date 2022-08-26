#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path

import clip
from ldb.plugins.clip_utils import (
    get_device, get_image_features
)


def main(argv) -> None:
    src_path = Path(argv[0])
    dst_path = Path(argv[1])
    device = get_device()

    # TODO: parametrize model name
    model, preprocess = clip.load("ViT-B/32", device=device)

    image_paths = list(src_path.glob("*[!.json]"))
    annotation_paths = [x.with_suffix(".json") for x in image_paths]
    annotations = [json.loads(x.read_text()) for x in annotation_paths]

    image_features = get_image_features(model, preprocess, device, image_paths)

    for n, annotation in enumerate(annotations):
        embedding = image_features[n].numpy().squeeze().tolist()
        annotation["clip-embedding"] = embedding

    for n, image_path in enumerate(image_paths):
        dst_image_path = dst_path / image_path.name
        shutil.copy(image_path, dst_image_path)
        dst_image_path.with_suffix(".json").write_text(
            json.dumps(annotations[n]))


if __name__ == "__main__":
    main(json.loads(sys.stdin.read()))
