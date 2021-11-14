
## LDB datasets

LDB defines datasets as collections of pointers to immutable data objects paired with optional annotations and metadata. 

Since datasets are just collections, LDB can modify them without moving the underlying data objects. To examine the physical data objects or annotations in dataset, it must be partially or fully instantiated (see `INSTANTIATE` below). 

LDB datasets support names with [a-Z0-9-\_] ANSI characters. LDB commands require dataset names to carry a mandatory `ds:` prefix, and alows for optional `.v[0-9]*` postfix that denotes a dataset version number.  

## LDB object identifiers

LDB identifies data objects by hashsum - which is a primary data object identifier. LDB treats copies of data samples in immutable storage as different paths to the same data object, and permits any such path to be used as a secondary object identifier. 

LDB identifies annotations for data objects based on the rules of the ingress format, and saves them internally. Annotations in LDB are paired to objects and are not directly addressable. It is, however, possible to specify annotation version for a data object, or instantiate annotations without related data samples. 
 
## LDB workspaces

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

## QuickStart 

QuickStart allows the individual user to begin working with LDB without explicit configuration. To that end, QuickStart makes strong configuration assumptions, and in return can jumpstart the LDB workflow with as little as 3-4 commands.

`STAGE` is the only LDB command that can trigger QuickStart. To do it, `STAGE` confirms the absence of an active LDB instance, and calls `INIT` to create a new LDB repository before proceeding with staging a dataset.

 Under the hood, QuickStart consists of the following three steps:

* New LDB instance is created in user's home directory: `~/.ldb/private_instance`
* Storage configuration defaults to wide-open settings: 
    * All cloud locations are permitted to host data objects.
    * A `read-add` folder is created in user's home directory (see `ADD-STORAGE`).
* An `auto-index` option is set in LDB config, permitting `ADD` to process previously unindexed storage (see `ADD`)
 
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

Since LDB assumes that storage objects are immutable, it never attempts to alter or move them. However, LDB may be required to push *new* files to storage if user chooses to source objects from ephemeral _fs_ paths (for example, from a personal workspace). Destination configured as `read-add` will permit LDB to automatically save such objects into immutable storage.

## flags

`--read-add` 

Storage location registered with this flag must allow for adding files. 

LDB supports at most one `read-add` location, and uses it to save _previously unseen_ local data files that `ADD` command may encounter outside the registered storage. Users can change or remove the `read-add` attribute by repeatedly adding locations with or without this flag. Attempt to add a second`read-add` location to LDB should fail prompting the user to remove the attribute from existing location first. 

`read-add` location should never be used to store any data objects that originate at cloud locations. Attempt to reference unregistered cloud location in `ADD` command will fail immediately.

    
*Use case:* 

```
$ ldb add-storage gs://add-storage --read-add 
  new storage location gs://add-storage successfully registered.

$ ldb add ./cat1.jpg
     warning: object 0x564d copied to gs://add-storage/auto-import220211-11/cat1.jpg
```

There is a location `gs://add-storage` registered with `read-add` attribute, and user tries to add file from a workspace into a dataset. If LDB does not have an object with identical hashsum already indexed, the `ADD` command copies `cat1.jpg` into `gs://add-storage` under the unique folder name, indexes it, and adds this object to dataset.

*Use case:* 

```
$ ldb add ./cat1.jpg
     error: object 0x564d is not in LDB and no read-add location configured
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
    

# INDEX \<storage folder URI(s) | storage object URI(s)\ | workspace folder> [flags]

`INDEX` updates LDB repository with data objects and annotations given as arguments. If LDB instance was created via QuickStart (see `STAGE`), then any cloud location may be indexed by default. If LDB instance was created with the `INIT` command, then LDB assumes indexed URIs to reside within storage locations configured (see `ADD-STORAGE`) and will fail otherwise. If folder is supplied to `INDEX` with no format flag, this folder is traversed recursively to recover objects and annotations in default format (one .json file per every data object sharing the object name). All hidden paths are excluded during indexing, which means any path where any of the directory or filenames begins with a dot (`.`) will not be indexed.

LDB maintains a "current" annotation version for every data object with at least one indexed annotation. LDB will update the "current" annotation version for a data object under the two following conditions:

 * This object is re-indexed (explicitly or implicitly), and an associated annotation for this data object was successfully recovered.
 * This annotation was not seen before (re-indexing older annotation versions will have no effect on LDB).

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
* `object-list` can be of one object identifier types: `0x<sum>` | `object_path` | `ds:<name>[.v<num>]` | `workspace_folder`

`ADD` is the main workhorse of LDB as it allows data sample(s) to be added to a dataset staged in the workspace. 

`ADD` builds a list of objects referenced by their hashsum, storage location, or source dataset, and applies optional filters to rectify this list. Objects passing the filters are merged into the currently staged dataset. When data object is added to the workspace, an associated annotation will go with it. The particular annotation version will be determined by the source identifier. In case of version collisions (same object re-added multiple times with divergent annotation versions), the latest annotation will be kept.

`ADD` allows for multiple objects (or object sets) of one type to be specified in one command. If no explicit object sources are provided, `ADD` assumes the source to be `ds:root` – which is all objects indexed by LDB.

While normally `ADD` references sources already known to LDB (pre-indexed objects with valid identifiers), it can also target a storage folder directly. In that case, `INDEX` command is automatically run over this folder to ensure the index is up to date. 

A special scenario for `ADD` arises when it targets ephemeral filesystem paths (anything outside the configured storage locations). Most commonly, such targets would be in the current workspace (where new objects were added directly, or where annotations were edited in-place). `ADD` can understand such changes and will save new data objects into permanent storage (see the `--read-add` option in `ADD-STORAGE`).

## object identifiers supported by `ADD`

1. `0x<sum>` - full hashsum of an object. Currently LDB uses MD5, so any MD5 hashsum that corresponds to an object indexed by LDB is a valid identifier.

*Use case:* 
```
$ ldb stage ds:cats ./
$ ldb add 0x456FED 0x5656FED    # result: objects id 0x456FED 0x5656FED added to dataset
```

2. `object_path` - any fully qualified (down to an object), or folder path within registered storage locations. Shell GLOB patterns are supported.

By default, `ADD` checks if the specified objects (or a list of objects recursively found in folder) were previously indexed by LDB, and uses the indexed annotations if this is the case. If some objects in the list are not found in index, `ADD` command fails with a reminder to run `INDEX` first.

*Use case:*
```
$ ldb stage ds:cats ./
$ ldb add gs://my-datasets/cats/black-cats/  # previously indexed location
  12 objects added to workspace (ds:cats)
```


*Use case:*
```
$ ldb stage ds:cats ./
$ ldb add gs://my-datasets/cats/white-cats/  # location is registered but folder contains new data
  error: 23 objects detected that are not found in ds:root
  Please run INDEX command first to process this storage location
```

This behavior can be altered with `auto-index` option in LDB configuration file. If set, this option allows `ADD` to implicitly `INDEX` to process objects in the folder or paths. This implicit call to `INDEX` assumes the objects are in the default format (one annotation file per each data objects), and will fail otherwise.

*Use case:*
```
$ ldb stage ds:cats ./
$ ldb add gs://my-datasets/cats/white-cats/  # location is registered but folder contains new data
  indexing gs://my-datasets/cats/white-cats/
  23 objects found, 20 new objects added to index, 3 annotations updated
  23 objects added to workspace (ds:cats)
```

3. `object_path` - any valid *fs* path NOT registered with `ADD-STORAGE`. The path can be fully qualified (down to objects), or reference a folder. When `ADD` is called on unregistered fs path, it expects annotations in default format and works in the following way:

  * If `object_path` is the workspace:
      -  `ADD` will process updated annotations even in absense of paired data objects (see `INSTANTIATE --annotations-only`)
      -  `ADD` will ignore data object previews (see `INSTANTIATE --preview`)
  
  * In all other cases:
      - If previously indexed data objects are found, they are added to staged dataset, alongside with their annotations
      - If new objects (unknown to LDB) are found and `read-add` storage option configured, those objects are copied to `read-add` storage, indexed, and then added.
      - If new objects (unknown to LDB) are found but no `read-add` storage configured, `ADD` command fails.
       
*Use case:*
```
$ ldb stage ds:cats ./
$ ldb instantiate --annotations-only
$ sed -i 's/class=cat/class=dog/g' cat1.json 
$ ldb add ./                  # result: annotation for cat1.jpg got a new version in LDB, and in ds:cats
```

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

5. `workspace_folder` - ADD can take a workspace folder name as an argument. This helps to avoid saving temporary datasets to LDB. 

*Use case:*
```
$ mkdir red_cats; cd red_cats
$ ldb stage ds:red_cats ./                     # create some temporary dataset 
$ ldb add ds:cats --query 'cat_color == red'   # fill it from some source
$ cd .. ; mkdir green_cats; cd green_cats      # create another dataset 
$ ldb stage ds:red_cats ./                     # create another temporary dataset
$ ldb add ds:cats --query 'cat_color == green' # fill it from another source
$ cd ..  
$ ldb stage ds:red_and_green_cats ./           # make a permanent dataset
$ ldb add ./red_cats ./green_cats              # merge two temporary datasets into it 
$ ldb commit                                   # save a permanent dataset
$ rm -rf green_cats/ red_cats/                 # delete temporary datasets

```

ADD with a `workspace_folder` argument can also be used to share datasets between different LDB instances. In this latter case, the only requirement is to ensure that destination LDB instance has access to all file paths of the source workspace.

## filters and modifiers supported by `ADD`

`ADD` can be called with several filter and modifier flags. If multiple flags are specified, filters will be pipelined, so their order may matter. Multiple instances of one flag are not permitted in one `ADD` command.


`--file <filesystem attributes query>`

Builds a query (see LDB Query Syntax) using fixed JSON fields specific to LDB index. The list is:

* MTIME - data object modification time. 
* A_MTIME - annotation modification time.
* INDEXED - data object first indexing time. Not affected by re-indexing (data objects are immutable).
* A_INDEXED - annotation last indexing time. Affected by re-indexing (annotations are mutable).
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

`--sort <model with arguments>`

Passes a list of objects through external program (or ML model) that sorts them according to match criteria. Often used with `--limit`. 

*Use case:*
```
$ ldb add --ml CLIP 'cat sitting on a chair' --limit 100 # returns 100 images that best match the provided semantic embedding
```

`--limit <integer>`

Cuts the input list of objects at \<integer\> samples.

`--sample <probability>`

Passes every object in input list with a given Bernoulli probability.

```
$ ldb add ds:cats --sample 0.9 
```

`--tag <string>`

Passes objects with referenced tag, equivalent to --query LDB_TAG == \<string\>


## LDB Query Language

Ability to construct complex queries is on of key features of LDB that permits it to extract data objects that are best suitable for training. LDB query language builds on top of [JMESPATH](https://jmespath.org) and supports JSON slices, projections, and reductions. This means, for example, that ML engineer can request only images with a given number of a particular class object detected.

More formally, queries are defined as:

```
QUERY:   TERM | TERM <AND | OR> QUERY
TERM:    JMESPATH operator TARGET
```
terms are optionally grouped by parentheses.


Where, 
* JMESPATH is any valid JMESPATH expression
* operator is one of:  `==`  `>`  `<` `!=` 
* TARGET is one of: `JMESPATH` `JSON_OBJECT` `STRING_REGEX` `NUMBER`

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

`SYNC` synchronizes workspace state with dataset instance found at \< target-folder \>. It acts as a combination of `ADD` and `DEL` commands and logically clones \<target-folder\> to staged dataset, effectively overwriting it.

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

`--preserve-paths`

Instantiate objects preserving full storage paths. Only supported for default LDB format (annotation file per every object).

`--preview [lambda_id]`

Preview flag instantiates data objects after passing them through a given lambda function (for example, downscaling to specific size for image previews). It has no effect if cloud storage does not support object lambdas, or code access point for `lambda_id` was not configured.

# COMMIT [message]

`COMMIT` takes the currently staged dataset and saves it to LDB. This action renders workspace "clean" – meaning that all changes are saved, and workspace can be erased if needed. The result of `COMMIT` command on "dirty" workspace is always a new version of dataset.

The optional `message` flag will be added as the commit message and shown in `ldb status` when called with a dataset as an argument.

# DIFF \<ds:\<name\>\> [ds:\<name\>]

`DIFF` prints a list of differences between two datasets. `DIFF` with one argument can only run from a workspace and uses as the first comparand.

# LIST  \< object-list \> [filters]

`LIST` can take the exact same arguments as `ADD` but only prints matching objects instead of actually adding them.
Unlike `ADD`, `LIST` without arguments targets objects in a staged dataset. To target objects in LDB index, use `ds-root` as the object source.

## flags

`-s` or  `--summary` 

just prints object counts

`-v` or  `--verbose`

detailed object information

# STATUS  [ds:\<name\>[.v<number>]

When run without arguments from a workspace, `STATUS` summarizes state of a staged dataset. This includes any uncomitted changes and current object counts. If called with an argument, `STATUS` prints a summary for a dataset in the argument.

# PULL [object-id(s)]

`PULL` changes annotation versions for indicated object(s) in workspace to latest known to LDB. If no `object-id(s)` specified, command will apply to all objects in a workspace.



