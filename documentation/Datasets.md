# LDB Datasets

LDB comes pre-configured with access to several public datasets:

* [Dogs and Cats](#dogs-and-cats)
* [TextOCR](#textocr)

### Dogs and Cats

Dataset containing 200 images of cats and dogs in ['strict-pairs'](Command-summary.md#index) format.
Schema looks as follows:

```
{
  "class": "dog",
  "id": "1020",
  "inference": {
    "class": "dog",
    "confidence": 0.3
  },
  "num_annotators": 4
}
```
**S3 url:**
* s3://ldb-public/remote/data-lakes/dogs-and-cats/

**Downloading as archive:**
* https://remote.ldb.ai/datasets/dogs-and-cats/dogs-and-cats.zip
* https://remote.ldb.ai/datasets/dogs-and-cats/dogs-and-cats.tar.gz

**Example of use:**
```
ldb index s3://ldb-public/remote/data-lakes/dogs-and-cats/
ldb stage ds:my-animals ./
ldb add s3://ldb-public/remote/data-lakes/dogs-and-cats/
ldb eval --limit 3 --query '[class, inference.class]'
ldb get ws:./ --pipe clip-text 'orange cats' --limit 10 -t orange-cats/
```

### TextOCR

A sample of the [TextOCR](https://textvqa.org/textocr/) dataset containing about 1800 images.

**Downloads:**
* https://remote.ldb.ai/datasets/textocr/textocr.zip
* https://remote.ldb.ai/datasets/textocr/textocr.tar.gz

**Example of use:**
```
ldb add-storage textocr
ldb index --format bare textocr
ldb list ds:root --summary
ldb list ds:root --query 'length(anns) >= `20`' --summary
ldb eval ds:root --limit 1 --query 'anns[*].utf8_string'
ldb list ds:root --query 'length(anns[?regex(utf8_string, `\\d`)]) >= `1`' --summary
```

## Download tips

Zip files and and gzipped tarballs are available for some public datasets to get started and play with LDB workflows. These can be downloaded from the URLs provided under [Datasets](#datasets) with a browser or with a CLI tool such as [DVC](https://dvc.org/doc/install):
```
dvc get-url https://remote.ldb.ai/datasets/DATASET_NAME/DATASET_NAME.zip
unzip DATASET_NAME.zip
```

Or download and unpack with `curl` and `tar`:
```
curl -L https://remote.ldb.ai/datasets/DATASET_NAME/DATASET_NAME.tar.gz | tar xz
```
