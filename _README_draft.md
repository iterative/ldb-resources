# β README

Label Database (**LDB**) is an **open-source** tool for **data-centric** AI and machine learning projects. It works **upstream from model training** and intends to index data in the *cloud storages* and *data lakes*, organizing pointers to data samples into datasets.

**LDB** aims to displace ad-hoc dataset management and de-duplication tools – such as file folders, spreadsheets and SQL databases. In the upstream direction, LDB can interface with labeling software, and in the downstream direction LDB integrates with ML pipelines. 

**Key LDB features**:

* unix-like **command line** instrument
* no changes to existing data storage. Data objects be stored anywhere in local storage, web, S3, Google Cloud, or Azure. There is **no need** to **move or duplicate** data objects in order to create, share or modify an LDB dataset.
* advanced manipulation and versioning for datasets. Collections can be cloned, queried, merged, and sampled. **Every change in a dataset is tracked**
* label-aware operations. Objects can be selected based on **annotation metadata, file attributes, or custom ML model queries**, and changes to ingress object metadata are versioned. 
* **reproducible,** **shareable, and fast to materialize**. A particular dataset version will always point to the same set of data objects and annotations. Data samples can be placed in a shared cache during instantiation, so transfers from remote locations are accelerated.

Full LDB command summary [here](documentation/Command-summary.md)

### Contents

- [How LDB works](#how-ldb-works)
- [Quick start](#quick-start)
- [Comparison to related technologies](#comparison-to-related-technologies)
- [Contributing to LDB](#contributing)


### How LDB works

Data objects in ML normally start life from data mining, data labeling, data cleansing, or data synthesis and accummulate at storage locations. LDB can index these locations and note unique data objects along with their annotations (if present). Queries into LDB index then can used to construct datasets that work like collections of pointers into the storage. Since LDB does not save data objects internally, it relies on persistent storage locations to access samples in the future. This means a read-only access into protected storage is sufficient for LDB, and LDB dataset operations can never endanger original data objects.

<img src="images/ldb-struct.png" width="500" height="288" align="left">

The main use case for LDB is to organize objects into collections (datasets) for training or testing. Datasets can then be shared and versioned within LDB, which makes collaboration on dataset membership (cloning, merging, splitting, adding, and removing objects) manageable and reproducible.

Since LDB datasets are logical, they must be materialized (instantiated) prior to use. Whenever a dataset needs to be materialized (for instance, to run a model experiment), LDB copies all relevant objects from storage and compiles the linked annotations. 

For as long as object storage remains intact and logical dataset state is saved within LDB, a physical dataset instance created by LDB can always be safely erased after the experiment is complete.

## Quick Start
Please refer to [sample LDB workflow](documentation/Getting-started-with-LDB.md) for more a detailed example of Data-driven AI methodology and to [LDB command summary](documentation/Command-summary.md) for additional information on command options.

<img src="images/warn.png" width="35" height="25" align="left">

**LDB instance** is a persistent structure where all information about known objects, labels and datasets is being stored. To set up a shared LDB instance for a team or organization, please follow [LDB team setup](documentation/Quick-start-teams.md). If no LDB instance is found, a private one will be created automatically in the `~/.ldb` directory the first time an LDB dataset is staged. 

| Step | Command |
| --- | --- |
| Install LDB | ```$ pip install 'ldb-alpha[clip-plugin,resnet-plugin]'``` |

### Forming datasets by querying annotations

Ability to issue complex queries is key to dataset formation in LDB.  For demo purposes, we will use a web-hosted image dataset with annotations in the following JSON format that denote animal class, size, and eye positions:

```json
{
  "class": "cat",
  "features": {
    "left-eye": {
      "x": 318,
      "y": 222
    },
    "right-eye": {
      "x": 340,
      "y": 224
    }
  },
  "size": "large"
}
```

| Step | Command |
| --- | --- |
| Cats size L | ```$  ldb get s3://ldb-public/remote/ds/cats/ --query 'size == `large`' large-cats``` |
| Small heads | ```$ ldb get ds:root --query 'sub(features."right-eye".x, features."left-eye".x) < `30`' small-head``` |

Now we should have folder `large-cats` with instantiated data samples annotated as `"size": "large"`, and folder `small-head` with samples annotated for horizontal distance between animal eyes less than 30 pixels. LDB can support very complex JSON queries that would normally require custom programming by making good use of extended JMESPATH query language (see [LDB queries](documentation/LDB-queries.md) for details).

<img src="images/warn.png" width="35" height="25" align="left">
LDB command `GET` in examples above does four distinct things: it creates a targer folder, stages a namesake dataset there, performs logical addition of objects mentioned in query, and instantiates the result.


* Note that objects in folders `large-cats` and `small-head` can be overlapping – for example, the same animal can be labeled `"size": "large"` but not occupy much real estate in the image. In that case, the same object will be present in both folders, yet LDB is smart enough to avoid double transfer and storage by using a local cache.

* Also note that the first query explicitly referenced cloud storage, while the second did not. LDB indexes unknown data objects at first encounter, so subsequent queries can run from the internal LDB index addressable under the reserved name "root".

### Forming datasets by querying object file attributes

At index time, LDB also stores object attributes that can be queried in the same way a conventional file search tool would work over storage. For example, LDB can filter objects for symbol matches in storage path and for creation timestamp range:

| Step | Command |
| --- | --- |
| Regex to object path | ```$ ldb get --path 'cat[0-9][0-3].*' misc-cats``` |
| Range of ctimes | ```$ ldb get --file 'fs.ctime < `"2022-03-28"`' --file 'fs.ctime > `"2022-03-25"`' misc-cats ``` |

* LDB index (ds:root) is a default source for objects, so LDB commands query all known objects unless instructed otherwise
* The first `GET` command stages new dataset 'misc-cats' in a namesake folder, and the second command adds to it.
* Time-based query uses two `--file` filters to intersect their results in order to form a time interval

### Query debugging

JMESPATH queries can quickly become complicated, so it is useful to understand how LDB constructs and evaluates them.

LDB treats any expression that results in null, boolean false, or an empty objects as 'falsy' that fails the filter, and treats every other output (including 0) as 'truthy' that passes the filter. Any reference to a non-existing key immediately fails the filter.

To understand exactly what LDB does in each case, it is useful to utilize command `EVAL` and observe the result of  JSON query reduction. `EVAL` without --query simply returns the entire annotation:

```
$ ldb eval 0xffa97795d32350dc450f41c4ce725886

0xffa97795d32350dc450f41c4ce725886
{
  "class": "cat",
  "features": {
    "left-eye": {
      "x": 318,
      "y": 222
    },
    "right-eye": {
      "x": 340,
      "y": 224
    }
  },
  "size": "small"
}
```

Any missing JSON key in query produces `null` – which means this query would immediately fail:

```
$ ldb eval 0xffa97795d32350dc450f41c4ce725886 --query 'inference.time'

RuntimeWarning: MissingIdentifierException: inference
0xffa97795d32350dc450f41c4ce725886
null
```
A valid JMESPATH expression will always emit a JSON value:
```
$ ldb eval 0xffa97795d32350dc450f41c4ce725886 --query 'class'

0xffa97795d32350dc450f41c4ce725886
"cat"
```

### Custom code for queries

If none of existing methods to query annotation or a data object works well, LDB supports custom query code that collects all objects passed through filters so far (see [command summary](Command-summary.md#pipe-plugins) for API reference). Here is an example of "useless" filter that sorts objects by their hashsum identifiers:

```python
# id_sorted.py

import json
import sys

if __name__ == "__main__":
    for data_object_hash, *_ in sorted(json.loads(sys.stdin.read())):
        print(data_object_hash, flush=True)
```

| Step | Command |
| --- | --- |
| Use of custom query filter | `$ ldb get --pipe python3 ./id_sorted.py --limit 3 misc-cats` |

### ML plugins for queries

One application of custom code is ML plugins that run supplementary ML models to identify objects of interest. LDB ships with CLIP and ResNet plugins for image filtering, but [other ML plugins](documentation/Plugins.md) can be easily added. This helps, for example, to find objects with features not present in annotations.

Here is an example of using CLIP semantic embedding to calculate which 10 images will have content closest to "orange cat":

| Step | Command |
| --- | --- |
| Change into workspace "misc-cats" | ```$ cd misc-cats```
| Add three images most resembling orange cats | ```$ ldb add ds:root --pipe clip-text 'orange cat' --limit 10``` |

* Note we used ADD command within the workspace that contains dataset `misc-cats`. ADD results in a logical membership change, so no actual files were copied into workspace. This is convenient in cases where the dataset is large and does not need an immediate instantiation.


### Instantiation

At this point, folder `misc-cats` holds a logical dataset `misc-cats` that is only partially instantiated. In particular, the "orange cat" images were not copied from storage. We can materialize this dataset entirely with `INSTANTIATE` command that renders a physical instance of a staged logical dataset:

| Step | Command |
| --- | --- |
| Materialize the entire dataset "misc-cats" | ```$ ldb instantiate``` |

* LDB uses caching to avoid re-downloading objects that were already instantiated by GET before


### Saving and versioning datasets

As we saw with `INSTANTIATE` and `ADD`, many LDB commands are designed to run within a workspace that holds a staged dataset. We can verify if the current folder is indeed a valid LDB workspace with command `STATUS`:

| Step | Command |
| --- | --- |
| Check the state of the workspace 'misc-cats' | `$ ldb status` |

As we see from the output, we are indeed in a workspace where a dataset 'misc-cats' was staged. However, this dataset has changes not yet saved into LDB. This is because the pending changes must be communicated to LDB with command `COMMIT` which pushes a new dataset version into the LDB instance:

| Step | Command |
| --- | --- |
| Save dataset 'misc-cats' into LDB | `$ ldb commit` |

Let as add more objects from another workspace that we created earlier:

| Step | Command |
| --- | --- |
| Add more objects | `$ ldb add ../large-cats/*png` |
| Check status again | `$ ldb status` |

* ADD can identify objects by reference to a dataset, workspace, hash ids, or a list of files
* If we save the current state of the workspace, it will create new version for dataset 'misc-cats':

| Step | Command |
| --- | --- |
| Save 'misc-cats' version 2 | `$ ldb commit` |
| Compare with previous | `$ ldb diff ds:misc-cats.v1` |

* LDB uses postfix notation `.vNN` to refer to specific version of a dataset

### Dataset mixing and matching

The combination of queries and commands `ADD` and `DEL` allows for arbitrary organization of data objects. Some examples:

| Step | Command |
| --- | --- |
| Stage a new dataset in a workspace | ```$ ldb stage --force new-cats``` |
| Add all objects from some named dataset into a workspace | `$ ldb add ds misc-cats.v2` |
| Subtract all objects from a named dataset from a workspace | `$ ldb del ds misc-cats.v1` |
| Fill shuffled objects from a source folder | ```$ ldb add ../small-head  --shuffle --limit 10'``` |

* STAGE with flag --force clobbers the contents of target folder
* To retain objects that are in one dataset but not another, it is sufficient to ADD the first and DEL the second

## Comparison to related technologies

One good question when considering a new ML tool is whether it is worth the investment of time to adopt. 

Without a tool like LDB, a team iterating on data typically takes one of the common recipes: (1) datasets as file folders, (2) datasets as spreadsheets, or (3) datasets under control of ML framework. All these solutions have their limits we discuss in the greater detail [here](/documentation/alternatives-to-LDB.md).

A second good question is why one should choose LDB over general data versioning (like [DVC](https://dvc.org/) or [PachyDerm](pachyderm.com)). The answer is that capabilities of LDB and general versioning systems do not overlap. 

For example, DVC actively manages the model repository and interprets datasets as cached files under full version control. On the other hand, LDB is an indexing service over immutable storage and treats datasets as collections of pointers. This lightweight approach relies on storage immutability to guarantee access, but offers higher speed and better flexibility. In addition, LDB understands annotations and can group sparse objects into datasets by queries.

If your data is indexed by LDB while your models are run by DVC, the two tools will happily work together, [see more recipes here](documentation/Getting-started-with-LDB.md).


## Contributing

```
TODO
```
