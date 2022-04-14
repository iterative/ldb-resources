# α README

Label Database (**LDB**) is an **open-source** tool for **data-centric** AI and machine learning projects. It works **upstream from model training** and intends to index data in the *cloud storages* and *data lakes*, organizing pointers to data samples into datasets.

**LDB** aims to displace ad-hoc dataset management and de-duplication tools – such as file folders, spreadsheets and SQL databases. In the upstream direction, LDB can interface with labeling software, and in the downstream direction LDB integrates with model-based ML pipelines. 

**Key LDB features**:

*  MLOps-grade **command line** experience. 
* Lightweight management of data sources. Data objects can exist anywhere in local storage, S3, Google Cloud, or Azure. There is **no need** to **move or duplicate** data objects in order to create, share or modify an LDB dataset (named collection of pointers).
* Advanced manipulation and versioning for datasets. Collections can be cloned, queried, merged, and sampled. **Every change in a dataset is tracked**, and provenance of constituent objects can be verified at all times.
* Label-aware operations. Objects can be selected based on **annotation metadata, file attributes, or custom ML model queries**, and changes to ingress object metadata are versioned. 
* **LDB datasets are reproducible,** **shareable, and fast to materialize**. A particular dataset version will always point to the same set of data objects and annotations. Data samples can be placed in a shared cache during instantiation, so transfers from remote locations are accelerated.

Full LDB command summary [here](documentation/Command-summary.md)

### Contents

- [Installation](#installation)
- [How LDB works](#how-ldb-works)
- [Quick start](#quick-start)
- [Comparison to related technologies](#comparison-to-related-technologies)
- [Contributing to LDB](#contributing)

## Installation

### pip **(PyPI core)**

```sh
pip install ldb-alpha
```

### installation with ML plugins **(optional)**

```sh
pip install 'ldb-alpha[clip-plugin,resnet-plugin]' 
```

### How LDB works

LDB indexes immutable storage locations and notes all unique data objects along with their associated annotations (if present). This index can then be queried to construct datasets that work like collections of sparse pointers into the storage. Note that LDB does not save data objects internally, and relies on persistent storage locations to serve data objects in the future. This means it is safe to give LDB access to storage as it never needs privileges to erase or modify data objects.

![ldb-intro](images/ldb-struct.png)

The main use case for LDB is to create and maintain persistent collections of cloud-based objects. These collections (datasets) are filled by logical queries into the index or other datasets (e.g. samples annotated with a certain class, created at given time, contains a given number of event instances, etc). 

Datasets can then be shared and versioned within LDB, which makes collaboration on dataset membership state (cloning, merging, splitting, adding, and removing objects) manageable and reproducible.

Whenever a dataset needs to be instantiated (for instance, to run a model experiment), LDB copies all relevant objects from storage into ephemeral workspace and compiles the linked annotations. Since storage is immutable and all dataset state is kept within LDB, this workspace can be safely erased after the experiment is complete.

## Quick Start
Please refer to [LDB workflow](documentation/Getting-started-with-LDB.md) for more a detailed example of Data-driven AI methodology.

**LDB instance** is a persistent structure where all information about known objects, labels and datasets is being stored. To set up a shared LDB instance for a team or organization, please follow [LDB team setup](documentation/Quick-start-teams.md). If no LDB instance is found, a private one will be created automatically in the `~/.ldb` directory the first time an LDB dataset is staged. 

### Creating datasets from querying annotations

Ability to issue complex queries is key to dataset formation in LDB.  For demo purposes, we will use a web-hosted dataset with annotations in the following JSON format:

```
{ 
  "class": "cat",
  "size": "large",
  "features": {"left-eye":{"x": 318, "y": 222}, "right-eye":{"x": 340, "y": 224}},
}
```

| Step | Command |
| --- | --- |
| Install LDB | ```$ pip install 'ldb-alpha[clip-plugin,resnet-plugin]'``` |
| Query cats size L | ```$  ldb work https://ldb.ai/ds/cats.json --query 'size == `large`' large-cats ``` |
| Cat heads < 30px in width | ```$ ldb work --query 'sub(features."right-eye".x,features."left-eye".x) < `30`' small-heads ``` |

Now we should have folder `"large-cats"` with instantiated data samples annotated as `"size": "large"`, and folder `"small-heads"` with samples annotated for horizontal distance between cat eyes less than 30 pixels. To run complex JSON queries, LDB supports extended JMESPATH language (see [LDB queries](documentation/LDB-queries.md) for details).

* Note that objects in folders `"large-cats"` and `"small-heads"` can be overlapping, but LDB uses local cache to avoid creation of multiple copies.
* Also note that the first query explicitly referenced cloud storage (web url), while the second did not. LDB indexes data objects at first encounter, so subsequent queries can run from internal LDB index.

### Creating datasets from querying data objects directly

Querying annotations and labels is not the only way to create datasets. In addition to specifying data objects by paths, file attributes and annotation features, LDB can use plugins to filter objects by features missing in annotations. For example, we can use semantic search through the index of cat images:

| Step | Command |
| --- | --- |
| Create dataset by ML query: | `$ ldb work --pipe clip-text 'orange cat' --limit 10 orange-cats` |

LDB ships with CLIP and ResNet plugins for image filtering, but [custom ML plugins](documentation/Plugins.md) can be added for other data types.

### Saving and versioning datasets

We have used `WORK` command in the previous section to create two folders, each with a collection of data objects and annotations. LDB refers to a folder that holds such collection as *workspace*. Most LDB commands run from within workspace, using it as a context.

A workspace can be made into a named dataset by saving it to LDB:

| Step | Command |
| --- | --- |
| Change into workspace | `$ cd ./large-cats` |
| Save this dataset into LDB | `$ ldb commit` |

Now dataset `ds:large-cats` is saved. Since LDB defines the dataset as a collection of data objects and annotations, a particular dataset version will always remain reproducible. 

If we change a dataset and save it again, this will create a new version, but we can still refer to the previous one if needed:

| Step | Command |
| --- | --- |
| Remove one data object | `$ ldb del ./cat1_008.jpg` |
| Save modified dataset into LDB | `$ ldb commit` |
| Compare to a previous version | `$ ldb diff ds:large-cats.v1` |

* Note LDB uses prefix `ds:` before dataset names and postfix `.vNN` to reference a particular dataset version.

### Workspace operations

| Step | Command |
| --- | --- |
| Add cat objects from index by annotation | ```$ ldb add ds:root —-query 'class == `cat`'``` |
| Check the status of a staged dataset | `$  ldb list`|

Note the use of single quotes to shield query from shell expansion, and the use of backticks to denote the literal value ("cat"). Also note that a special name `ds:root` designates the entire LDB index which references all known objects. 

LDB is also not limited to querying the existing annotations. If installed, [custom ML plugins](documentation/Plugins.md) can be employed for queries beyond JSON:

| Step | Command |
| --- | --- |
| Add objects by ML query: | `$ ldb add ds:root --pipe clip-text 'orange dog' --limit 10` |
| Check the status of a staged dataset | `$ ldb list`|

At this point, our workspace holds membership info for all cat images from sample dataset, and ten images that best resemble an orange dog. It is okay to have same objects added to a dataset multiple times as LDB automatically deduplicates. Once we are happy with results, this dataset can be instantiated (materialized) in the desired output format to examine the samples or train the model.


### Dataset algebra

How many objects in `"large-cats"` and `"large-heads"` are the same? 
There are many ways to answer this question, but one way is to use LIST command to query a workspace. 

| Step | Command |
| --- | --- |
| Index images from storage | `$ ldb index ~/dogs-and-cats` |

### Annotation versioning

How many objects in `"large-cats"` and `"large-heads"` are the same? 
There are many ways to answer this question, but one way is to use LIST command to query a workspace. 

| Step | Command |
| --- | --- |
| Index images from storage | `$ ldb index ~/dogs-and-cats` |

### Storage indexing and object tags

| Step | Command |
| --- | --- |
| Instantiate all objects into the workspace | `$ ldb instantiate `|
| See the resulting physical dataset | `$ ls`|

After examining the actual data objects, one might decide to add or remove data samples, or to edit their annotations.
LDB can pick the resulting changes right from the workspace:


### Advanced queries and query debugging




### Instantiation and reindexing options




## Comparison to related technologies

One good question when considering a new ML tool is whether it is worth the investment of time to adopt. 

Without a tool like LDB, a team iterating on data typically takes one of the common recipes: (1) datasets as file folders, (2) datasets as spreadsheets, or (3) datasets under control of ML framework. All these solutions have their limits we discuss in the greater detail [here](/documentation/alternatives-to-LDB.md).

A second good question is why one should choose LDB over general data versioning (like [DVC](https://dvc.org/) or [PachyDerm](pachyderm.com)). The answer is that capabilities of LDB and general versioning systems do not overlap. 

For example, DVC actively manages the model repository and interprets datasets as cached files under full version control. On the other hand, LDB is an indexing service over immutable storage and treats datasets as collections of pointers. This lightweight approach relies on storage immutability to guarantee access, but offers higher speed and better flexibility. In addition, LDB understands annotations and can group sparse objects into datasets by queries.

If your data is indexed by LDB while your models are run by DVC, the two tools will happily work together. DVC can recognize LDB datasets as data sources, and LDB can utilize the shared DVC cache. 


## Contributing

```
TODO
```
