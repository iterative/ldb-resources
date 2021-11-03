
## LDB datasets

LDB defines datasets as collections of pointers to data objects in immutable storage locations, paired with optional annotations and metadata. 

Since datasets are just collections, LDB can modify them without moving the underlying data objects. To examine the physical data objects or annotations in dataset, it must be partially or fully instantiated (see `INSTANTIATE` below). 

LDB datasets support names with [a-Z0-9-\_] ANSI characters. LDB commands require dataset names to carry a mandatory `ds:` prefix, and alows for optional `.v[0-9]*` postfix that denotes a dataset version number.  

## LDB object identifiers

LDB identifies data objects by hashsum - which is a primary data object identifier. LDB treats copies of data samples in immutable storage as different paths to the same data object, and permits any such path to be used as a secondary object identifier. 

LDB identifies annotations for data objects based on the rules of the ingress format, and saves them internally. Annotations in LDB are paired to objects and are not directly addressable. It is, however, possible to specify annotation version for a data object, or instantiate annotations without related data samples. 
 
## LDB workspace

To work on a dataset, LDB stages it in a workspace (see `STAGE` below). Workspace holds all information for a dataset that is being modified. One user might have several workspaces in different directories. Any changes to a dataset (adding & removing objects, changing tags, etc) remain local to workspace until the `COMMIT` 

Here is the internal structure of a workspace folder:
```
.ldb_workspace/
            ├── collection/
            └── workspace_dataset    
```

Most LDB commands – `ADD`, `DEL`, `SYNC`, `INSTANTIATE`, `COMMIT`, `TAG`, `PULL` target only a staged dataset, and hence must run from a valid workspace. Other commands – like `LIST`, `STATUS`, `DIFF` will also target a staged dataset by default.

## locating an LDB instance

Every LDB command is linked to an instance where datasets and annotations are stored. There are two ways to locate an instance:

1. Set `core.ldb_dir` in the global configuration file `~/.ldb/config` to an absolute path.
```
[core]
ldb_dir = '/some/absolute/path'
```
2. Set the `LDB_DIR` environment variable to any absolute or relative path.

If both ways of configuration are present, the environment variable takes precedence.
If no method of configuration succeeds, all LDB commands will fail, except for `INIT` which does not require an existing installation, and `STAGE` when used in QuickStart (see below).

## Quickstart 

QuickStart allows the individual user to begin working with LDB without explicit configuration. To that end, QuickStart makes strong configuration assumptions, and in return brings tangible value in as little as 3-4 commands.

`STAGE` is the only LDB command that can trigger QuickStart. To do it, `STAGE` confirms the absence of an active LDB instance, and calls `INIT` to create a new LDB repository before proceeding with staging a dataset.

 Under the hood, QuickStart process consists of the following two steps:

* LDB instance is created in the user's home directory: `~/.ldb/private_instance`
* Default storage configuration is created with wide-open settings: 
    * All cloud locations are permitted to host data objects.
    * A `read-add` folder is created in user's home directory (see `ADD-STORAGE`).
 
Below is an example of QuickStart, where user queries a remote storage in two commands right after the LDB installation:

```
$ ldb stage ds:my-numerals 
$ ldb add gs://iterative/roman-numerals --query 'class == "i"'
```

# INIT \<directory\>

`INIT` creates a new LDB instance (repository) in the given directory. For most enterprise installations, LDB repository folder would be a shared directory on a fast disk. `INIT` does not attempt to locate an active LDB instance, and permits a new LDB repository to reside anywhere in a filesystem.

In addition to creating an LDB instance, `INIT` makes a global configuration file at `~/.ldb/config` and sets the `core.ldb_dir` key to point to new LDB location. If configuration files already exist, `INIT` does not change them.

Running `ldb init <path>` creates the following directory structure:
```
path/
├── data_object_info/
├── datasets/
└── objects/
    ├── annotations/
    ├── collections/
    └── dataset_versions/
```
After finishing, `INIT` prints the summary of work and a reminder on how to change active LDB instance pointers.

## flags

`-f` or  `--force` 

If a target directory already contains an existing LDB instance,  `INIT` fails & prints a reminder to use `--force`.  Using `-f` or  `--force` erases an existing LDB installation.

If the target directory contains data (but not an LDB instance), `INIT` fails without an option to override. The user must provide an empty directory.


# ADD-STORAGE \<storage-URI\>

`ADD-STORAGE` registers a disk (or cloud) data storage location into LDB and verifies the requisite permissions. 

LDB keeps track of storage locations for several reasons, the primary being engineering discipline (prevent adding objects from random places), and authentication (see `access configuration` below). 

LDB supports the following storage URI types: fs, Google Cloud, AWS, and Azure. 

The minimum and sufficient set of permissions for LDB is to **list, stat and read** any objects at `<storage-URI>`. `ADD-STORAGE` fails if permissions are not sufficient, and succeeds with a warning if permissions are too wide. `ADD-STORAGE` also checks if `<storage-URI>` falls within an already registered URI, and prints an error if this the case. Permissions are re-checked if an existing storage location is re-added.

Since LDB assumes that storage is immutable, it never attempts to alter or move files in storage. However, LDB may be required to push files to storage (under unique paths), which happens if user wants data samples sourced outside the configured storage (for example, from personal workspace). Destination configured as `read-add` will permit LDB to copy such samples into storage.

## flags

`--read-add` 

Storage location registered with this flag must allow for adding files. 

LDB supports at most one `read-add` location, and uses it to save _previously unseen_ local data files that `ADD` command may encounter outside the registered storage. Users can change or remove the `read-add` attribute by repeatedly adding locations with or without this flag. Attempt to add a second`read-add` location to LDB should fail prompting the user to remove the attribute from existing location first. 

`read-add` location should never be used to store any data objects that originate at cloud locations. Attempt to reference unregistered cloud location in `ADD` command will fail immediately.

    
*Use case:* 

```
(workspace)$ ldb add-storage gs://add-storage --read-add 
  new storage location gs://add-storage successfully registered.

(workspace)$ ldb add ./cat1.jpg
     warning: object 0x564d copied to gs://add-storage/auto-import220211-11/cat1.jpg
$
```

There is a location `gs://add-storage` registered with `read-add` attribute, and user tries to add file from a workspace into a dataset. If LDB does not have an object with identical hashsum already indexed, the `ADD` command copies `cat1.jpg` into `gs://add-storage` under the unique folder name, indexes it, and adds this object to dataset.

*Use case:* 

```
(workspace)$ ldb add ./cat1.jpg
     error: object 0x564d is not in LDB and no read-add location configured
$
```
There are no `read-add` storage locations registered, and user tries to add a file from his workspace to a dataset. If LDB does not have an object with identical hashsum already indexed somewhere in storage, the ADD command fails.

## access configuration

TODO document storage access configuration here

TODO object lambda access configuration here


# STAGE \<ds:\<name\>[.v\<number\>]\>  \<workspace_folder\>

`STAGE` command creates an LDB workspace at a given `<workspace_folder>` for dataset `<name>`. The destination folder is expected to be empty. If LDB repository has no dataset `<name>`, a new dataset is created. If `<name>` references an existing dataset, it is staged out (but not automaticlly instantiated).

If workspace is not empty, `STAGE` checks if it holds a clean dataset, and clobbers it.  If `<workspace_folder>` holds a dirty dataset, a warning and a status of this dataset are printed before failure. If `<workspace_folder>` is not empty but does not hold an LDB dataset, a reminder to use `--force` is printed. 

*Use case:* 

```
$ ldb stage ds:cats ./
$ ldb status
 Dataset ds:cats, 0 objects, not saved in LDB.
```

If `STAGE` cannot locate an active LDB instance, it assumes a QuickStart, and proceeds with setting a new LDB instance (see QuickStart discussion).
    
## flags

`-f` or  `--force` 

allows to clobber the workspace regardless of what is there.
    

# INDEX \<storage folder URI(s) | storage object URI(s)\> [flags]

`INDEX` updates LDB repository with data objects and annotations given as arguments. If the LDB instance was created via quickstart with the `STAGE` command, then any location may be indexed. If a shared LDB instance was created with the `INIT` command, then LDB assumes URIs to reside within storage locations configured (see `ADD-STORAGE`) and will fail otherwise. If folder is provided and no format flag specified, this folder is traversed recursively to recover objects and annotations in default format (one .json file per every data object sharing the object name).

All hidden paths are excluded during indexing. This means any path where any of the directory or filenames begins with a dot (`.`).

LDB maintains a current annotation version for every data object where at least one associated annotation has been indexed. LDB will update the current annotation version for a data object only under the following conditions:
 * An annotation for the data object is found during indexing
 * The discovered annotation is new, meaning LDB has not indexed an identifical annotation for the same data object before

_Use case:_
```
$ ldb index gs://my-storage/new-folder  # traverse this folder to find data objects in default format
```

_Use case:_
```
$ ldb index gs://my-storage/cat1.json   # index (or reindex) a specific annotation URI
```

## flags

`--format < folder-labels | label-studio | COCO | OpenImage | ImageNet >`  -  sets schema for data objects and annotations. `INDEX` fails if URI is not conformant with schema.

# ADD  \< object-list \> [filters]

Where,
* `object-list` is one or more arguments of the following object identifier types: `0x<sum>` | `object_path` | `ds:<name>[.v<num>]`
* A single `ADD` call may only use one of these types. For example you may pass multiple datasets, but not both a dataset and an object hashsum.

`ADD` is the main workhorse of LDB as it allows users to add any data sample(s) to the currently staged workspace dataset from various sources. 

`ADD` builds a list of objects referenced by their hashsum, storage location, or source dataset, and applies optional filters to rectify this list. Objects passing the filters are merged into the currently staged dataset.

By default, when a data object is added to the workspace dataset, an associated annotation will be added with it. If datasets are passed to `ADD`, the annotations in those dataset will be used, giving preference to the last dataset argument. Otherwise LDB identifies the current annotation for the data object in the root dataset, if any, and uses it. See the `INDEX` command about how the current annotation is set. If a data object is already a member of the workspace dataset and it is added, its annotation will be updated according to this policy. This includes removing a data objects annotation if a dataset is added where that data object has not annotation.

When a data object is added from a dataset, an annotation may be added with it. If the object comes from a dataset

By default, a data object's default annotation is included. For datasets, the default annotation is simply the annotation in the dataset. During indexing, LDB sets the default annotation for a data object to the last unique annotation indexed for that data object.

`ADD` allows for multiple objects (or object groups) of one type to be specified in a command. If no sources for objects are provided, `ADD` assumes source to be `ds:root` – all objects indexed by LDB.

While normally `ADD` references sources already indexed by LDB (such objects in a dataset, or pre-indexed objects via valid identifiers), it can also target a storage folder directly. In that case, `INDEX` command is automatically run over this folder to ensure the index is up to date. 

A special case for `ADD` arises when targeting ephemeral filesystem (fs) paths outside of configured storage locations. Most commonly, such a target would be a current workspace where new objects were added directly, or where some annotations were edited in-place. `ADD` can understand such changes and does the right thing to manage data samples and annotations (this mode of operation is only supported for annotations in the default LDB format, see the `--read-add` option in `ADD-STORAGE` for discussion).


## object identifiers supported by `ADD`

1. `0x<sum>` - full hashsum of an object. Currently LDB uses MD5, so any MD5 hashsum that corresponds to an object indexed by LDB is a valid identifier.

*Use case:* 
```
$ ldb stage ds:cats ./
$ ldb add 0x456FED 0x5656FED    # result: objects id 0x456FED 0x5656FED added to dataset
```

2. `object_path` - any fully qualified (down to an object), or folder path in registered storage locations. If `object-path` is fully qualified, LDB tries to get object hashsum and match it to known objects. If hashsum was not seen before, LDB falls back to `INDEX` the object. If `object-path` is a folder, `ADD` calls `INDEX` immediately and then recursively processes indexed objects in path. 

In all cases of `INDEX` involvement within `ADD`, it will fail if objects are not in default format. 

```
$ ldb stage ds:cats ./
$ ldb add gs://my-datasets/cats/white-cats/  # location is registered but folder contains unindexed data
  indexing gs://my-datasets/cats/white-cats/
  23 objects found, 20 new objects added to index, 3 annotations updated
  23 objects added to workspace (ds:cats)
```

3. `object_path` - any valid *fs* path NOT registered with `ADD-STORAGE`. The path can be fully qualified (down to objects), or reference a folder. When `ADD` is called on unregistered fs path, it expects annotations in default format and works in the following way:

  * If `object_path` is the workspace:
      -  `ADD` will process updated annotations even without paired data objects (see `INSTANTIATE --annotations-only`)
      -  `ADD` will ignore "preview" data objects (see `INSTANTIATE --preview`)
       
*Use case:*
```
$ ldb stage ds:cats ./
$ ldb instantiate --annotations-only
$ sed -i 's/class=cat/class=dog/g' cat1.json 
$ ldb add ./                  # result: annotation for cat1.jpg got a new version in LDB, and in ds:cats
```
  
  * In all cases:
      - If previously indexed data objects are found, they are added to staged dataset, alongside with annotations
      - If new objects (unknown to LDB) are found and `read-add` storage option configured, those objects are copied to `read-add` storage, indexed, and then added to dataset.
      - If new objects (unknown to LDB) are found but no `read-add` storage configured, `ADD` command fails.

*Use case:*
```
$ ldb stage ds:cats ./
$ cp ~/storage/cat1.jpg ./   # bring some object already in LDB but not in this dataset
$ ldb add ./cat1.jpg         # result: staged dataset ds:cats now includes cat1.jpg
```

*Use case:*
```
$ ldb stage ds:cats ./
$ cp ~/Downloads/cat1.jpg ./  # this object is not in LDB and read-add storage location configured
$ ldb add ./                  # result: cat1.jpg copied to read-add storage, and then added
```



4. `ds:<name>[.v<num>]` - dataset name with an optional version number. Any valid LDB dataset can serve as a source of objects. Note that every dataset has objects paired with a particular annotation number, so it is possible to build a list where the same object is referenced several times with different annotations. If this is the case, the collision is resolved by using the latest annotation version among references.

*Use case:*
```
$ ldb stage ds:cats
$ ldb add ds:black_cats ds:white_cats.v2  # merged with latest ds:black_cats and v.2 of ds:white_cats
```

## filters supported by `ADD`

`ADD` can be called with several filter flags. If multiple flags are specified, filters will be pipelined, so their order may matter. Multiple filters of one type are not permitted in one `ADD` command.

`--file <filesystem attributes query>`

Builds a query (see LDB Query Syntax) using fixed JSON fields specific to LDB index. The list is:

* MTIME - data object modification time. 
* A_MTIME - annotation modification time.
* INDEXED - data object first indexing time. Not affected by re-indexing (data objects are immutable).
* A_INDEXED - annotation last indexing time. Affected by re-indexing (annotations are mutable).
* A_VERSION - sets an explicit LDB annotation version.
* U_VERSION - sets an explicit user-defined annotation version.
* SIZE - data object file size in Kilobytes, Megabytes or Gigabytes (qualifier K, M or G).
* PATH - data object path. If same data object was indexed under multiple paths, will match either one.
* NAME - data object name. If same data object was indexed under multiple names, will match either one.

*Use case:*
```
$ ldb add --file 'PATH == "gs:datasets/cat-bucket/.*"'  # Object source is implicitly ds:root, filtered by regex
```

`--query <annotation query terms>`

Permits a query (see LDB Query Syntax) that references arbitrary JSON fields present in object annotation.

*Use case:*
```
$ ldb add --query 'class == "cats"'
```

`--ml <model with arguments>`

Passes a list of objects through an ML model that sorts them according to match criteria. Often used with `--limit`. 

*Use case:*
```
$ ldb add --ml CLIP 'cat sitting on a chair' --limit 100. # returns 100 images that best match semantic embedding
```

`--limit <integer>`

Cuts the input list of objects at \<integer\> samples.

`--sample <probability>`

Passes every object in input list with given Bernoulli probability.

```
$ ldb add ds:cats --sample 0.9 
```

`--tag <string>`

Passes objects with referenced tag, equivalent to --query TAG == \<string\>


## LDB Query Language

LDB Query is defined as:

```
QUERY:   TERM | TERM <AND | OR> QUERY
TERM:    JMESPATH operator TARGET
```
terms are optionally grouped by parentheses.


Where, 
* JMESPATH is any valid [JMESPATH](https://jmespath.org) expression
* operator is one of:  `==`  `>`  `<` `!=` 
* TARGET is one of: `JSON_OBJECT` `STRING_REGEX` `NUMBER`

Examples of LDB queries:

```
*.classes[0:1] == {["cats", "dogs"]}
```

```
( *.classes[0] != "cat.*" ) AND ( length(*.classes) < 5 )
```


# DEL \< object-list \> [filters]

`DEL` takes the same arguments and filters as `ADD`, but instead of adding the filtered objects it subtracts them from dataset staged in the workspace. If objects provided to `DEL` are not in the dataset, `DEL` does nothing.

# TAG [text-tag text-tag ...]  \< object-list \> [filters]

`TAG` is a text string in ANSI character set [0-9A-z-\_]. Multiple tags can be attached to datasets or individual objects. Tags attached to objects are inherited – which means they will exist on all instances of an object in all datasets irrespective of their annotations. Tags attached to datasets are not inherited - which means, objects added from a dataset featuring a particular tag will not carry this tag forward.

`TAG` takes the same arguments and filters as `ADD` command to identify datasets or individual objects to apply tags.

## flags 

`--remove`  removes indicated tags from objects or datasets

# SYNC \< target-folder \>

`SYNC` synchronizes workspace state with dataset instance found at \< target-folder \>. It acts as a combination of `ADD` and `DEL` commands and logically clones \<target-folder\> to staged dataset, overwriting it.

_Use case:_
```
$ ldb instantiate ./     # instantiate the workspace dataset
$ rm cats1.jpg           # delete one object file
$ ldb sync ./            # pick up changes in workspace
```

# INSTANTIATE [\< object id(s) \>] [flags]

`INSTANTIATE` partially or fully re-creates dataset in a workspace. If valid `object id(s)` are given, only those objects (with annotations) are instantiated. This command works whether the dataset in the workspace is committed (clean) or not (dirty). To partially reconstruct the dataset, `INSTANTIATE` can take any valid object ids - hashsums or full object paths.

## flags
 
`--annotations`, `--annotations-only`

Only instantiates annotations (no data objects). Can be combined with `--format`

`--format <name>`

Specific annotation output format. The list of formats mirror those in `INDEX` command with `--format` flag.

`--preserve-names`

Instantiate objects preserving full storage paths. Only supported for default LDB format (annotation file per every object).

`--preview [integer]`

Preview dataset instantiates data objects using a specific lambda function (for example, downscaling to specific size for image previews). Has no effect if storage does not support object lambdas, or code access points are not configured.

# COMMIT [message]

`COMMIT` takes the currently staged dataset and saves it to LDB. This action makes workspace "clean" – meaning that all changes are saved, and workspace can be erased if needed. The result of `COMMIT` command on "dirty" workspace is a new version of dataset.

The optional `message` flag will be added as the commit message and shown in `ldb status` when called with a dataset as an argument.

# DIFF \<ds:\<name\>\> [ds:\<name\>]

`DIFF` prints a list of differences between two datasets. `DIFF` with one argument can only run from a workspace and assumes the first comparand to be staged dataset.

# LIST  \< object-list \> [filters]

`LIST` can take exact same arguments as `ADD` but only prints matching objects instead of actually adding them.
Unlike `ADD`, `LIST` without arguments targets objects in a staged dataset. To target objects in LDB index, use `ds-root` as the object source.

# STATUS  [ds:\<name\>[.v<number>]

When run without arguments from a workspace, `STATUS` summarizes the state of a staged dataset. This includes any uncomitted changes and current object count. If called with an argument, `STATUS` prints a summary for a dataset in the argument.

# PULL [object-id(s)]

`PULL` changes annotation versions for indicated object(s) to latest version in LDB. If no `object-id(s)` specified, applies to all objects in a dataset.



