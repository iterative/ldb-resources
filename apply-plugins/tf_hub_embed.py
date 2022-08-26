#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import tensorflow_hub as hub
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img


def main(argv, std_in) -> None:
    if len(argv) != 2:
        print(
            "usage: tf_hub_embed.py <tf_hub_url> <output_embedding_name>",
            file=sys.stderr,
        )
        sys.exit(1)
    src_dir, dst_dir = json.loads(std_in)

    src_path = Path(src_dir)
    dst_path = Path(dst_dir)
    
    model = hub.KerasLayer(argv[0])

    image_paths = list(src_path.glob("*[!.json]"))
    annotation_paths = [x.with_suffix(".json") for x in image_paths]
    annotations = [json.loads(x.read_text()) for x in annotation_paths]
    
    image_features = []
    for image_path in image_paths:
        # TODO: Get target_size from model
        image = load_img(image_path, target_size=(192, 192))
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)
        image_features.append(model(image))

    for n, annotation in enumerate(annotations):
        embedding = image_features[n].numpy().squeeze().tolist()
        annotation[argv[1]] = embedding

    for n, image_path in enumerate(image_paths):
        dst_image_path = dst_path / image_path.name
        shutil.copy(image_path, dst_image_path)
        dst_image_path.with_suffix(".json").write_text(
            json.dumps(annotations[n]))


if __name__ == "__main__":
    main(sys.argv[1:], sys.stdin.read())
