# α README

Label Database (**LDB**) is an **open-source** tool for **data-centric** AI and machine learning projects. It works **upstream from model training** and organizes data in *cloud storages* and *data lakes* into reproducible datasets.

**LDB** aims to displace ad-hoc dataset management, data search and de-duplication tools – such as file folders, spreadsheets, and custom code for data selection/augmentation. In the upstream direction, LDB can interface with labeling software, and in the downstream direction LDB provides data files for clean training and evaluation pipelines – including modern registry-based model cards.

**Key LDB features**:

* **command line tool** (MLOps oriented). 
* LDB manages datasets as versioned collections of pointers into storage locations with automatic de-duplication
* Since LDB datasets use pointers, there is **no need** to **move or copy** data objects to create, share or modify datasets
* LDB datasets are purely logical, so they are easily cloned, merged, sliced, and sampled
* **Search in the cloud:** data objects can be selected based on JSON annotations, file attributes, or helper ML model queries 
* **Annotation tracking:** JSON annotations are tracked and versioned during indexing
* **Reproducibility and sharing:** every LDB dataset version always points to the same collection of data samples and can be easily shared
* **Cloud optimization:** LDB caches objects during instantiation, increasing speed and reducing cloud egress costs

### Contents

- [Installation](#installation)
- [How LDB works](#how-ldb-works)
- [What LDB can do](#what-ldb-can-do)
- [LDB commands](#ldb-commands)
- [LDB versus other versioning tools](#ldb-versus-other-versioning-tools)
- [Contributing to LDB](#contributing)

## Installation

### pip **(PyPI core)**

```sh
pip install ldb-alpha
```

### installation with AWS and ML plugin support **(optional)**

```sh
pip install 'ldb-alpha [s3,clip-plugin,resnet-plugin]' 
```

### add anonymous access to public s3 datasets **(optional, only needed for [LDB team setup](documentation/Quick-start-teams.md))**
```
ldb add-storage s3://ldb-public/remote/ -o anon true
```
Sample datasets [are here](documentation/Datasets.md)

Full LDB command summary [is here](documentation/Command-summary.md)


### How LDB works

LDB indexes immutable storage and notes unique data objects along with their associated annotations (if present). This index can then be queried to construct datasets that operate like collections of sparse pointers into the storage. LDB does not save data objects internally, and depends on their persistent storage locations to materialize (instantiate) datasets on demand.


<img src="images/LDB-graph.png"  width=50% height=50%>

LDB datasets can then be shared and versioned, which makes any membership changes (cloning, merging, splitting, adding, and removing objects) manageable and reproducible.

Whenever a dataset needs to be instantiated (for instance, to run a model experiment), LDB copies all relevant objects from cloud storage into the local workspace and recreates all linked annotations. Since storage is immutable and dataset state is kept within LDB, the local workspace can be safely erased after the experiment is complete. 

TODO: LDB supports local caching of instantiated data, so sucessive object materializations do not need to repeat cloud transfers.

## What LDB can do

<details>
  <summary>Cloud data retrieval and de-duplication</summary>
  

🦉 
The simplest way to form a dataset from cloud and materialize it in LDB is by using the [GET](documentation/Command-summary.md#get) command, which can point to cloud location, index it, add data objects into a specified dataset and instantiate it in one shot: 

```
ldb get s3://ldb-public/remote/data-lakes/dogs-and-cats/ -t animals
  
  Staged ds:.temp.2022-06-07T00:46:33.865467+00:00 at 'animals'
  Adding to working dataset...
  Added 200 data objects to ds:.temp.2022-06-07T00:46:33.865467+00:00
  Instantiating data...

  Copied data to workspace.
    Data objects:       200
    Annotations:        200

```
At this point, a public path s3 path was indexed, and 200 objects added to temporaty dataset in folder `animals`, after which the dataset was materialized. Let's try to add the same objects again to see how automatic de-deduplication works:

  ```
  cd animals
  ldb add s3://ldb-public/remote/data-lakes/dogs-and-cats/
  
    Adding to working dataset...
    Added 0 data objects to ds:.temp.2022-06-07T00:46:33.865467+00:00
  ```
LDB reads the contents of path but adds no new objects because it recognizes all input objects as duplicates.
  
🦉
</details>

<details>
  <summary>Find and retrieve data samples by file attributes</summary>
  

🦉 Searching data by name patterns and file attributes is easy in filestystems with `find(1)` and similar tools, but is not readily available in the cloud. LDB fills this gap by storing file attributes in JSON format at indexing time and allowing to query them with JMESPATH expressions.

  For one example, time-based file search of object in LDB index can look like this:

```
  ldb list ds:root --file 'fs.mtime > `2022-03-03`'
 
```
  
  For another example, retrieval based on the regular expression match in the path can look like this:
  
  
```
ldb get --path 'dog\.102[0-2]+' s3://ldb-public/remote/data-lakes/dogs-and-cats/ -t some-animals
  
```
  
LDB stores file attributes collected during indexing in a JSON schema, so in the example above, flag `--path` is actually a shortcut for JMESPATH regex function applied to JSON `fs.path` attribute (equivalent to ```--file 'regex(fs.path, `EXPR`)'```.  
  
  <details>
    <summary>Sample LDB-indexed file attributes</summary>

  🪶
  ``` 
         ldb eval  id:98603fb145b88c265fb4a745e6aaf806   --file '@'

            id:98603fb145b88c265fb4a745e6aaf806
            {
              "alternate_paths": [
                {
                  "fs_id": "",
                  "path": "ldb-public/remote/data-lakes/dogs-and-cats/dog.1020.jpg",
                  "protocol": [
                    "s3",
                    "s3a"
                  ]
                }
              ],
              "first_indexed": "2022-06-07T03:00:54.270212+00:00",
              "fs": {
                "atime": null,
                "ctime": null,
                "fs_id": "",
                "gid": null,
                "mode": 0,
                "mtime": null,
                "path": "ldb-public/remote/data-lakes/dogs-and-cats/dog.1020.jpg",
                "protocol": [
                  "s3",
                  "s3a"
                ],
                "size": 26084,
                "uid": null
              },
              "last_indexed": "2022-06-07T03:00:54.270212+00:00",
              "last_indexed_by": "dkh",
              "tags": [],
              "type": "jpg"
            }
  ```

  🪶
  </details>

File attribites schema works just like any other JSON, for example JMESPATH `--file` queries can be pipelined and use comparators and functions:
  
  ```
  ldb list ds:root --file 'fs.protocol[0] == `s3`' --file 'type == `jpg` && fs.size < `20000`'
  ```
  
🦉
</details>

<details>
  <summary>Retrieve data samples by querying JSON annotations</summary>


🦉 LDB relies on AWS JMESPATH language to query JSON annotations. JMESPATH is not a Turing-complete language, but it is compact and sufficiently expressive to cover most operations normally achieved custom coding. JMESPATH is fundamentally a JSON expressions reducer, and is extensible with custom functions.
    
Most everyday data selection tasks appear simple and elegant in JMESPATH. For example, choose objects with confidence below a threshold:

  ```
  ldb list --query 'inference.confidence < 0.3
  ```
  Or, to compute the total area of all (possibly overlapping) bounding boxes for all images in workspace:
  
  ```
  ldb eval --query 'dotproduct(b_boxes[*].width, b_boxes[*].height))'
  ```
Please refer to the [queries](documentation/LDB-queries.md) document for more examples on JMESPATH expressions.
  
🦉
</details>
 

## LDB commands

<details>
  <summary>LDB command cheat sheet</summary>
  
🦉 
> **LDB instance** is a persistent structure where all information about known objects, labels and datasets is being stored. If no LDB instance is found, a private one will be created automatically in the `~/.ldb` directory the first time an LDB dataset is staged. To set up a shared LDB instance for a team or an instance in a different location, please follow [LDB team setup](documentation/Quick-start-teams.md).
 
>**LDB dataset** is a collection of pointers into storage. 

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

 TODO BETA: **Granular annotation versioning**

 | Step | Command |
 | --- | --- |
 | Add object with particular label version | `$  ldb add —-label-version 2 aws://my-awesome-bucket/1.jpg ` |
 | Bump label version for an object to latest | `$   ldb add aws://my-awesome-bucket/1.jpg` |
 | Bump all labels in a dataset to latest | `$ ldb pull`|

🦉
</details>

Full LDB command summary [is here](documentation/Command-summary.md)
## LDB versus other versioning tools

Without a program like LDB, engineers iterating on data commonly accept one of the following data management recipes: (1) datasets as file folders, (2) datasets as pointers stored in spreadsheets (or database records), or (3) datasets under control of ML frameworks. All these solutions have their limits we discuss in greater detail [here](/documentation/alternatives-to-LDB.md).

Datasets can also exist under general versioning tools like (like [DVC](https://dvc.org/) or [PachyDerm](pachyderm.com)). The disadvantage of general versioning is in destruction of the original storage layout. For example, DVC when manages the model repository, it takes ownership of data and stores the actual data samples in cache. 

On the opposite, LDB is an indexing service, and treats datasets as collections of pointers. This lightweight approach relies on storage immutability, but accepts the data in the original storage format (folders, names, etc), and permits LDB to operate without write access to cloud. In addition, LDB understands annotations and can group sparse objects into datasets by annotation queries. This forms a natural boundary between dataset managers and model/experiment management tools like DVC: LDB controls datasets, while DVC manages the rest of ML pipeline.  

## Contributing

Contributions are welcome! Pre-beta testers, please contact us for access.

