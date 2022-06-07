# α README

Label Database (**LDB**) is an **open-source** tool for **data-centric** AI and machine learning projects. It works **upstream from model training** and intends to index data in the *cloud storages* and *data lakes*, organizing pointers to data samples into datasets.

**LDB** aims to displace ad-hoc dataset management and de-duplication devices – such as file folders, spreadsheets, SQL databases and dataloader configurations. In the upstream direction, LDB can interface with labeling software, and in the downstream direction LDB integrates with model-based ML pipelines. 

**Key LDB features**:

* **command line** (MLOps oriented). 
* Datasets are defined as collections of pointers into storage locations, where **every change is tracked**
* Since datasets use pointers, there is **no need** to **move or duplicate** actual data objects to create, share or modify datasets
* LDB datasets are easily cloned, merged, splitted, and sampled
* **Annotation-aware workflow**. Objects can be selected based on JSON metadata, file attributes, or custom ML model queries, and all changes to annotations are versioned. 
* **LDB datasets are fully reproducible,** **shareable, and fast to materialize**. A particular dataset version will always point to the same set of data objects and annotations. Data samples can be placed in a shared cache during instantiation, so transfers from remote locations are accelerated.

### Contents

- [Installation](#installation)
- [How LDB works](#how-ldb-works)
- [Quick start](#quick-start)
- [LDB versus other versioning tools](#ldb-versus-other-versioning-tools)
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

### sample dataset with curl **(optional)**
```
curl -L https://remote.ldb.ai/datasets/dogs-and-cats/dogs-and-cats.tar.gz | tar xz
```

More sample datasets [here](documentation/Datasets.md)

Full LDB command summary [here](documentation/Command-summary.md)


### How LDB works

LDB indexes immutable storage and notes unique data objects along with their associated annotations (if present). This index can then be queried to construct datasets that work like collections of sparse pointers into the storage. LDB does not save data objects internally, and depends on their persistent storage locations to materialize (instantiate) datasets on demand.

![ldb-intro](images/ldb-struct.png)

The main use case for LDB is to create and maintain sparse collections of cloud-based objects. These collections (datasets) are filled by logical queries into the index or into other datasets (e.g. samples with certain file attributs, annotated with a certain class, created at given time, containing a given number of event instances, etc). 

LDB datasets can then be shared and versioned, which makes any membership changes (cloning, merging, splitting, adding, and removing objects) manageable and reproducible.

Whenever a dataset needs to be instantiated (for instance, to run a model experiment), LDB copies all relevant objects from storage into the local workspace and recreates all linked annotations. Since storage is immutable and dataset state is kept within LDB, the local workspace can be safely erased after the experiment is complete.

<details>
  <summary>LDB cheat sheet</summary>
  
🦉
 
 **LDB instance** is a persistent structure where all information about known objects, labels and datasets is being stored. If no LDB instance is found, a private one will be created automatically in the `~/.ldb` directory the first time an LDB dataset is staged. To set up a shared LDB instance for a team or an instance in a different location, please follow [LDB team setup](documentation/Quick-start-teams.md).
 
**LDB dataset** is a collection of pointers into storage. 

 ### Staging a new dataset 

 Whenever a new dataset is required – or an existing dataset needs an update, it must first be staged in an empty folder (data workspace). Staging does not automatically instantiate the dataset, but creates a draft state of dataset membership info and metadata. LDB prefixes dataset names with `ds:`

 | Step | Command |
 | --- | --- |
 | Create a workspace folder | `$ mkdir working-dataset; cd working-dataset` |
 | Create a new dataset in the workspace | `$  ldb stage ds:my-cats ./` |
 | Check the status of staged data | `$  ldb status ` |

 While working in this workspace, all subsequent dataset manipulations will apply to the staged dataset. 

 Logical modifications to dataset staged in the workspace are usually made with ADD and DEL commands that may reference individual objects, other datasets, and employ annotation queries (see [LDB queries](documentation/LDB-queries.md) for details).

 **Configuring immutable storage locations (optional)**

 LDB assumes data samples live in immutable locations from which they are indexed. By default, a private instance will treat any cloud location as immutable, and any local filesystem path as ephemeral. LDB automatically attempts to copy data samples from ephemeral locations into internal storage (defaults to `~/.ldb/read_add_storage`) during indexing. To prevent this behavior while indexing local storages, register them with `ADD-STORAGE` command:


 | Step | Command |
 | --- | --- |
 | Register some immutable storage location  | `$  ldb add-storage ~/dogs-and-cats` |

 Please remember that LDB is an indexing service. If you move or erase indexed data samples from storage, LDB index may break.

 ### Indexing storage folder

 Once the storage location is registered, it can be indexed. During indexing, LDB recognizes all unique objects and associates them with annotations (if present). Whenever new samples are added, their location must be reindexed for LDB to pick the changes. Annotations updated for the old data objects will be registered with a new version.

 | Step | Command |
 | --- | --- |
 | Index images from storage | `$ ldb index ~/dogs-and-cats` |

 ### Modifying a dataset

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

 ### Instantiation

 | Step | Command |
 | --- | --- |
 | Instantiate all objects into the workspace | `$ ldb instantiate `|
 | See the resulting physical dataset | `$ ls`|

 After examining the actual data objects, one might decide to add or remove data samples, or to edit their annotations.
 LDB can pick the resulting changes right from the workspace:

 ### Notifying LDB on workspace modifications

 | Step | Command |
 | --- | --- |
 | Edit some annotation     | `$ sed -i 's/dog/cat/g' dog-1088.json` |
 | Inject a new annotated sample directly into workspace | `$ cp ~/tmp/dog-1090.* ./`
 | Pick object and annotation changes from workspace | `$ ldb add ./`|

 To save staged dataset into LDB (with all the cumulative changes made so far), one needs to use the *commit* command.

 ### Dataset saving and versioning

 | Step | Command |
 | --- | --- |
 | Push a new version of staged dataset to LDB | `$ ldb commit` |

 Every new commit creates a new dataset version in LDB. By default, a reference to an LDB dataset assumes the latest version. Other dataset versions can be explicitly accessed with a version suffix:

 | Step | Command |
 | --- | --- |
 | Stage a particular version of a dataset | `$  ldb stage ds:my-cats.v3` |
 | Compare current workspace to a previous dataset version | `$  ldb diff ds:my-cats.v2`|

 If newer annotations will become available for the data object, they can be readded to dataset by name. If all labels need to be updated, this can be done with the *pull* command.

 ### TODO Granular annotation versioning

 | Step | Command |
 | --- | --- |
 | Add object with particular label version | `$  ldb add —-label-version 2 aws://my-awesome-bucket/1.jpg ` |
 | Bump label version for an object to latest | `$   ldb add aws://my-awesome-bucket/1.jpg` |
 | Bump all labels in a dataset to latest | `$ ldb pull`|

🦉
</details>
 
 
## LDB versus other versioning tools

Without a program like LDB, a team iterating on data commonly takes one of the following dataset recipes: (1) datasets as file folders, (2) datasets as spreadsheets (or database records), or (3) datasets under control of ML framework. All these solutions have their limits we discuss in greater detail [here](/documentation/alternatives-to-LDB.md).

Datasets can also exist under general model versioning tools like (like [DVC](https://dvc.org/) or [PachyDerm](pachyderm.com)). The disadvantage of this approach is general versioning destroys the original data storage structure. For example, DVC actively manages the model repository, hiding the actual files in cache. 

On the opposite, LDB is an indexing service over immutable storage, and treats datasets as collections of pointers. This lightweight approach relies on storage immutability, but keeps the data in the original form (storage folders, names, etc). In addition, LDB understands annotations and can group sparse objects into datasets by annotation queries. This forms a natural tool boundary: LDB manages datasets, while DVC manages the rest of ML pipeline.  

## Contributing

```
Contributions are welcome! Pre-beta testers, please contact us for access.
```
