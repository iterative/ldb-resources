# α README

Label Database or **LDB** is an **open-source** tool for **data-centric** science and machine learning projects. It works **upstream from model training** and intends to organize **data in your existing storage or data lake** into logical datasets.

**LDB** aims to displace ad-hoc dataset management and de-duplication tools – such as file folders, spreadsheets and SQL databases. In the upstream direction, LDB can interface with labeling software, and in downstream direction LDB integrates with model-centric pipelines. 

**Key LDB features**:

1. MLOps-grade **command line** experience. Does not require installing and maintaining any databases. 
2. Lightweight management of data sources. Data objects can exist anywhere in S3, Google Cloud, Azure or local storage, and datasets are defined as collections of pointers to these objects. There is **no need to move or duplicate data objects** in order to create, share or modify datasets. 
3. Advanced management and versioning of datasets. Datasets can be cloned, queried, merged, and sampled. **Every change in a dataset is tracked**, so provenance of constituent objects can be verified at all times.
4. Label-aware operations. **Objects can be selected based on their annotation metadata**, and changes to object metadata are versioned. 
5. **LDB datasets are reproducible,** **shareable, and fast to materialize**. A particular dataset version will always point to the same set of data objects and annotations. Datasets are cached during instantiation, so subsequent transfers from cloud locations are accelerated.

### Contents

- [How LDB works](#how-ldb-works)
- [Quick start](#quick-start)
    - [Setting a new LDB instance and indexing data objects](#setting-new-ldb-instance)
    - [Staging, creation and modification of datasets](#staging-a-dataset-into-workspace)
    - [Working with versions of labels and datasets](#dataset-versioning)
    - [Instantiation and caching]()
- [Some examples](#examples)
- [Installation](#installation)
- [Comparison to related technologies](#comparison-to-related-technologies)
- [Contributing to LDB](contributing-to-LDB)

### How LDB works

LDB indexes immutable storage locations and notes all unique data objects along with their associated annotations (if present). This index can then be queried to construct datasets that would look like collections of sparse pointers into the storage:

![ldb-intro](images/ldb-intro.png)

The simplest use case for LDB arises when a data scientist wants to create and maintain a persistent collection of cloud-based objects that are grouped into virtual datasets by some logical criteria (e.g. annotated with a certain class, created at given time, or satisfy a particular name pattern, etc). 

These virtual datasets can then be shared and versioned within LDB, which makes collaboration on dataset membership state (cloning, merging, splitting, adding, and removing objects) easily manageable and reproducible.

Whenever a virtual dataset needs to be instantiated (for instance, to run a model experiment), LDB copies all relevant objects from storage into the model workspace. Since storage is immutable and all dataset membership state is kept within LDB, the workspace can be safely erased after the experiment is complete.

## Quick Start

Please refer to Getting Started with LDB for a full version of this document.

LDB instance is a persistent structure where all information about known objects, labels and datasets is being stored. Typically there is one LDB instance per team or organization. 

### Setting new LDB instance

LDB assumes data objects are immutable and live in the pre-defined storage locations (cloud buckets or folders). You can add new storage locations to LDB at any time, but you cannot remove storage locations that are already referenced in the existing datasets. 

| Step | Command |
| --- | --- |
| Create a new LDB instance | `$  ldb init /data/myLDB` |
| Save LDB location into environment | `$  export LDB_ROOT=/data/myLDB` |

### Registering LDB storage locations

| Step | Command |
| --- | --- |
| Add a storage location | ` $  ldb add-storage gs://my-awesome-bucket/` |
| Verify current LDB storage locations | `$  ldb status` |

Once LDB is up and running, it can rebuild the index whenever new objects or annotations become available. Note, that LDB indexes only unique data objects (ignoring duplicates), and registers new label versions only if it encounters annotation updates.

### Indexing and re-indexing storage

| Step | Command |
| --- | --- |
| Index new objects in a storage folder | `$  ldb index gs://my-awesome-bucket/new-data/` |
| Verify that new objects appear in index | `$  ldb list ds:root` |

Whenever a new dataset is required or an existing dataset needs an update, it must first be staged in the model workspace. Staging does not automatically instantiate the dataset, but creates a draft state of the dataset membership info and all metadata:

### Staging a dataset into workspace

| Step | Command |
| --- | --- |
| Create a new dataset in the workspace | `$  ldb stage ds:my-new-dataset ./` |
| Check the status of staged data | `$  ldb status ` |
| List all objects in current workspace | `$  ldb list `|

All subsequent dataset manipulations will apply to the staged dataset. Logical modifications to dataset staged in the workspace are usually made with ADD and DEL commands that may reference individual objects, other datasets, and employ annotation queries (see LDB queries for details.

### Modifying a dataset

| Step | Command |
| --- | --- |
| Add objects from another ds by class | `$  ldb add ds:ImageNet —query *class == "cat"` |
| Remove all recently created objects | `$  ldb del —file mtime -1` |
| Check status of staged dataset | `$  ldb list`|


Staged dataset can be listed and instantiated, but modifications to it are not saved into LDB yet. To save the currently staged dataset into LDB (with all the cumulative changes made so far), one needs to use the *commit* command.

Every new commit bumps a dataset version in LDB. By default, every reference to an LDB dataset will assumes the latest version committed. Older dataset versions can be explicitly accessed with a version suffix:

### Dataset versioning

| Step | Command |
| --- | --- |
| Push a new version of staged dataset | `$  ldb commit` |
| Stage a particular version of a dataset | `$  ldb stage ds:my-cats.v3` |
| Compare workspace to dataset version | `$  ldb diff ds:my-cats.v2`|

If a dataset includes annotated objects, they will be paired with labels that were current at time of the object addition. If newer annotations become available later, updated objects can be re-added to dataset. If all labels need to be updated, this can be done with the *pull* command.

### Annotation versioning

| Step | Command |
| --- | --- |
| Add an object with particular label version | `$  ldb add gs://my-awesome-bucket/1.jpg —label-version 2` |
| Bump label version for an object to latest | `$   ldb add gs://my-awesome-bucket/1.jpg` |
| Bump all labels in a dataset to latest | `$   ldb pull`|

To examine contents of a data object (or an associated annotation), they need to be instantiated (copied from storage into workspace). Instantiation can be done for the entire dataset, or for separate objects. Instantiation re-creates annotations for objects that have them. 

### Instantiation

| Step | Command |
| --- | --- |
| Instantiate named dataset into folder | `$  ldb instantiate ds:my-great-dataset  /experiments/1` |
| Instantiate one object by hashsum ref| `$  ldb instantiate 0xFFABBDE23` |
| Instantiate all objects in workspace | `$  ldb instantiate`|


LDB cache is an optional feature that maintains shadow copies of objects previously instantiated. Cache speeds up workflows that involve fully or partially overlapping datasets by eliminating redundant transfers of data objects from storage. Read more about it in Configuring LDB Cache.

## Examples

```diff
- Create a subset of ImageNet dataset
- Merge cat images from COCO and ImageNet
- Create a new class category in COCO dataset using ML model
- Speed up teamwork with caching
- Identify and solve potential data quality issues
```

## Comparison to related technologies

A fair question when considering a new ML tool is whether it is worth the investment of time and effort to adopt. This section discusses some LDB alternatives.

First and foremost, **LDB is focused on data-driven ML cycles**. This means it is most useful when data corpus is dynamic, and where the model is expressive enough to benefit from improved data samples and annotations. 

Without the use of LDB, an organization facing the problem of training on better data typically attempts to organize their data sources into datasets by one of the following three recipes:

1. Folder-level dataset organization.

The default method for data organization in new ML projects is to create datasets by grouping data objects into named file folders. This method has an advantage of being the simplest way to bootstrap a new project, yet it comes with serious limitations:

* Experimenting on data (adding or removing data objects) results in multiple copies of the *same* dataset with minimal changes – which is undesirable for datasets of non-trivial sizes.

* Folders are not easy to slice and dice, and retain no metadata to keep track of the object provenance (which data sample came from which source dataset). 

* Attempts to add new data objects may result in repetitions (same object under multiple names in one dataset), or data loss (data objects overwritten due to collisions in namespace).

* Annotation updates are not tracked, which may result in annotations going stale.

* Folder-level datasets are difficult to integrate with privacy policies and directives (like GDPR) that often require data storage to be immutable and limited to approved providers.

2. Spreadsheets, or other database-powered datasets design.

A reasonable step up from managing datasets in file folders is to organize them data in spreadsheets filled with object pointers (URIs of data objects living in cloud locations). 

This method permits for sparse datasets, where individual objects are no longer required to reside in one folder or cloud bucket. Since spreadsheet-based datasets decouple storage from organization, they no longer require objects to be copied or moved to form new datasets, allow to store provenance meta-information as attributes, and can be made compatible with storage privacy directives. In addition, versioning for datasets and annotations can be provided for by means of storing multiple linked tables.

Spreadsheets, however, still carry significant limitations: 

* Spreadsheets do not solve the problem of repetitions (same data objects listed under different URIs), and cannot prevent annotations from going stale. Both of these functions require tracking objects by content, which spreadsheets cannot do natively.

* Spreadsheets do not provide native means to parse and query annotations alongside with their data objects. This means an ML engineer needs to compose the datasets manually, or use separate ad-hoc software to query annotations and export lists of the matching objects into spreadsheets and tables.

* Use of spreadsheets and databases to document datasets forces ML engineers to use unfamiliar tools that are hard to integrate into MLOps. Forming a dataset and registering it in a database becomes a manual chore with many touching points.

3. Heavyweight ML frameworks.

It is fairly common to find parts of functionality offered by LDB in the large, heavyweight ML frameworks. For example, any data labeling software suite likely has some function to track annotation versions and search annotations by fields. Likewise, every end-to-end ML platform facilitates organization of input data into the datasets, at least at the folder level. 

While heavyweight ML platforms can be very successful in vertical-specific applications, they are difficult to recommend as one-size-fits-all tools.

Unlike these platforms, LDB follows Unix toolchain philosophy and solves exactly one problem – it sits between the (immutable) data storage and mutable model training workspace, and allows for reproducible and fast data-driven ML iteration cycles. This allows for easy integration with MLOps and for compatibility with any labeling software upstream and arbitrary experiment automation software downstream.

## Installation

### pip **(PyPi)**

```bash
pip install ldb
```

### brew **(Homebrew/Mac OS)**

```bash
brew install ldb
```

## Contributing

```diff
- boilerplate contribution call to action
```
