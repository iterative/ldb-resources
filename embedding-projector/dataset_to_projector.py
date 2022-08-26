import csv
import json
import sys
from math import ceil, sqrt
from pathlib import Path

from PIL import Image


def main(input_folder, output_folder, label_field, embedding_field) -> None:
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True, parents=True)
    
    image_paths = list(input_path.glob("*[!.json]"))
    annotations = [
        json.loads(x.with_suffix(".json").read_text()) for x in image_paths]

    with open(output_path / "metadata.tsv", "w") as f: 
        f.writelines(
            "\n".join(x[label_field] for x in annotations)
        )

    with open(output_path / "embeddings.tsv", "w") as f:
        csv_writer = csv.writer(f, delimiter="\t")
        for annotation in annotations:
            csv_writer.writerow(annotation[embedding_field])

    num_images = ceil(sqrt(len(image_paths)))
    square_size = 100
    sprite_side = square_size * num_images
    sprite = Image.new(
        mode="RGBA",
        size=(sprite_side, sprite_side),
        color=(0,0,0,0)
    )
    for n, image_path in enumerate(image_paths):
        image = Image.open(str(image_path)).resize((square_size, square_size))
        div, mod = divmod(n, num_images)
        h_loc = square_size * div
        w_loc = square_size * mod
        sprite.paste(image, (w_loc, h_loc))

    sprite.save(str(output_path / "sprite.png"))
    (output_path / "projector_config.json").write_text(
        json.dumps(
            {
            "embeddings": [
                {
                "tensorName": input_path.name,
                "tensorShape": [
                    len(annotations), len(annotation[embedding_field])
                ],
                "tensorPath": "embeddings.tsv",
                "metadataPath": "metadata.tsv",
                "sprite": {
                    "imagePath": "sprite.png",
                    "singleImageDim": [square_size, square_size]
                }
                }
            ],
            "modelCheckpointPath": "Embeddings"
            },
            indent=4
        )
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
