# LDB Datasets

## Downloading

Zip files and and gzipped tarballs are available for some public datasets to get started and play with LDB workflows. These can be downloaded from the URLs provided under [Datasets](#datasets) with a browser or with a CLI tool such as [DVC](https://dvc.org/doc/install):
```
dvc get-url https://remote.ldb.ai/datasets/DATASET_NAME/DATASET_NAME.zip
unzip DATASET_NAME.zip
```

Or download and unpack with `curl` and `tar`:
```
curl -L https://remote.ldb.ai/datasets/DATASET_NAME/DATASET_NAME.tar.gz | tar xz
```

## Datasets

* [Dogs and Cats](#dogs-and-cats)
* [TextOCR](#textocr)

### Dogs and Cats

A dataset containing 200 images of cats and dogs.

**Downloads:**
* https://remote.ldb.ai/datasets/dogs-and-cats/dogs-and-cats.zip
* https://remote.ldb.ai/datasets/dogs-and-cats/dogs-and-cats.tar.gz

**Example:**
```
ldb add-storage dogs-and-cats
ldb index dogs-and-cats
ldb eval ds:root --limit 10 --query '[class, inference.class]'

mkdir my-workspace
cd my-workspace
ldb stage ds:orange-cats
ldb add ds:root --pipe clip-text 'orange cats' --limit 10
```

### TextOCR

A sample of the [TextOCR](https://textvqa.org/textocr/) dataset containing about 1800 images.

**Downloads:**
* https://remote.ldb.ai/datasets/textocr/textocr.zip
* https://remote.ldb.ai/datasets/textocr/textocr.tar.gz

**Example:**
```
ldb add-storage textocr
ldb index --format bare textocr
ldb list ds:root --summary
ldb list ds:root --query 'length(anns) >= `20`' --summary
ldb eval ds:root --limit 1 --query 'anns[*].utf8_string'
ldb list ds:root --query 'length(anns[?regex(utf8_string, `\\d`)]) >= `1`' --summary
```
