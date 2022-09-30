## LDB datasets

LDB defines datasets as collections of pointers to immutable data objects paired with optional annotations and metadata. 

Since datasets are just collections, LDB can modify them without moving the underlying data objects. To examine the physical data objects or annotations in dataset, it must be partially or fully instantiated (see `INSTANTIATE` below). 

LDB datasets support names with `[A-Za-z0-9_-]` ANSI characters. LDB commands require dataset names to carry a mandatory `ds:` prefix, and allows for optional `.v[0-9]*` postfix that denotes a dataset version number.

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

Most LDB commands – `ADD`, `DEL`, `SYNC`, `COMMIT`, `PULL` require a staged dataset, and hence must run from a valid workspace. Other commands – like `LIST`, `STATUS`, `DIFF` – will also target a staged dataset by default, but do not require a staged dataset if they are passed other dataset identifiers.

If the dataset is create with `STAGE`, it already has a name. Datasets staged with `GET` are unnamed, and will get a name at a first commit.

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

`STAGE` and `GET` (by means of calling `STAGE`) are the only two LDB command that can trigger QuickStart. To do it, `STAGE` confirms the absence of an active LDB instance, and calls `INIT` to start a new LDB repository before proceeding with staging a dataset.

 Under the hood, QuickStart consists of the following three steps:

* New LDB instance is created in user's home directory: `~/.ldb/private_instance`
* Storage configuration defaults to wide-open settings: 
    * All cloud locations are permitted to host data objects.
    * A `read-add` folder is created in user's home directory (see `ADD-STORAGE`).
* An `auto-index` option is set in LDB config, permitting `ADD` to process previously unindexed storage (see `ADD`)
 
Below is an example of QuickStart, where user queries a remote storage in two commands right after the LDB installation:

```
$ ldb stage ds:my-numerals 
$ ldb add gs://iterative/roman-numerals --query 'class == `i`'
```
### LDB command list

- [INIT](#init)
- [ADD-STORAGE](#add-storage)
- [STAGE](#stage)
- [INDEX](#index)
- [ADD](#add)
- [DEL](#del)
- [TAG](#tag)
- [SYNC](#sync)
- [TRANSFORM](#transform)
- [INSTANTIATE](#instantiate)
- [GET](#get)
- [COMMIT](#commit)
- [DIFF](#diff)
- [LIST](#list)
- [STATUS](#status)
- [PULL](#pull)
- [DS](#ds)
- [EVAL](#eval)
- [QUERY](#query)
- [UNINDEX](#unindex)
- [COMPLETION](#completion)

# INIT 

```
ldb init [-f] <path>
```

Initialize a new ldb instance at the given `<path>`.

`INIT` creates a new LDB instance (index) in the given directory. For most enterprise installations, LDB repository folder would be a shared directory on a fast disk. `INIT` ignores any existing LDB instances, and permits a new LDB repository to reside anywhere in a filesystem.

In addition to creating an LDB instance, `INIT` makes a global configuration file at `~/.ldb/config` and sets the `core.ldb_dir` key to point to new LDB location. If configuration files already exist, `INIT` does not change them.

Running `ldb init <path>` creates the following directory structure:
```
path/
├── config
├── custom_code/
│   ├── ldb_user_filters/
│   └── ldb_user_functions/
├── data_object_info/
├── datasets/
├── objects/
│   ├── annotations/
│   ├── collections/
│   ├── dataset_versions/
│   └── transforms/
└── storage
```
After finishing, `INIT` prints the summary of work and a reminder on how to change active LDB instance pointers.

## flags

`-f` or  `--force` 

If a target directory already contains an existing LDB instance,  `INIT` fails & prints a reminder to use `--force`.  Using `-f` or  `--force` erases an existing LDB installation.

If the target directory contains data (but not an LDB instance), `INIT` fails without an option to override. The user must provide an empty directory.


# ADD-STORAGE 

```
ldb add-storage [-a {true,false}] [-f] [-o <key> <value>] <path>
```

`ADD-STORAGE` registers a disk (or cloud) data storage location into LDB and verifies the requisite permissions. `<path>` should be a URI or a prefix for URIs.

LDB keeps track of storage locations for several reasons, the primary being engineering discipline (prevent adding objects from random places), and authentication (see `access configuration` below). 

LDB supports the following storage URI types: fs, Google Cloud, AWS, and Azure. 

The minimum and sufficient set of permissions for LDB is to **list, stat and read** any objects at `<path>`. `ADD-STORAGE` fails if permissions are not sufficient, and succeeds with a warning if permissions are too wide. `ADD-STORAGE` also checks if `<path>` falls within an already registered URI, and prints an error if this the case. Permissions are re-checked if an existing storage location is re-added.

Since LDB assumes that storage objects are immutable, it never attempts to alter or move them. However, LDB may be required to push *new* files to storage if user chooses to source objects from ephemeral _fs_ paths (for example, from a personal workspace). Destination configured as `read-add` will permit LDB to automatically save such objects into immutable storage.

## flags

`-o / --option <key> <value>`

Specify a key/value to pass to the fsspec filesystem instance created when accessing this storage location. May be used multiple times. Note that `value` is expected to be a JSON value in order to distinguish between different data types, but non-JSON values will be interpreted as a raw string. For example, to use a specific AWS profile with an s3 storage location, these are equivalent:

```
ldb add-storage s3://bucket/some/prefix -o profile '"profile-name"'
ldb add-storage s3://bucket/some/prefix -o profile \"profile-name\"
ldb add-storage s3://bucket/some/prefix -o profile profile-name
```

Or to access a public bucket anonymously (`true` will be converted to an actually bool value):
```
ldb add-storage s3://bucket/some/prefix -o anon true
```

`-a {true,false}, --read-add {true,false}`

Storage location registered with `--read-add=true` must have write-access to allow new files to be added. 

LDB supports at most one `read-add` location, and uses it to save _previously unseen_ local data files that `ADD` command may encounter outside the registered storage. Users can change or remove the `read-add` attribute by repeatedly adding locations with or without this flag. Attempt to add a second`read-add` location to LDB should fail prompting the user to remove the attribute from existing location first. 

`read-add` location should never be used to store any data objects that originate at cloud locations. Attempt to reference unregistered cloud location in `ADD` command will fail immediately.


*Use case:* 

```
$ ldb add-storage gs://add-storage --read-add true
  new storage location gs://add-storage successfully registered.

$ ldb add ./cat1.jpg
     warning: object id:564d copied to gs://add-storage/auto-import220211-11/cat1.jpg
```

There is a location `gs://add-storage` registered with `read-add` attribute, and user tries to add file from a workspace into a dataset. If LDB does not have an object with identical hashsum already indexed, the `ADD` command copies `cat1.jpg` into `gs://add-storage` under the unique folder name, indexes it, and adds this object to dataset.

*Use case:* 

```
$ ldb add ./cat1.jpg
     error: object id:564d is not in LDB and no read-add location configured
```
There are no `read-add` storage locations registered, and user tries to add a file from his workspace to a dataset. If LDB does not have an object with identical hashsum already indexed somewhere in storage, the ADD command fails.

## lambda configuration

TODO BETA 
document object lambda access configuration here


# STAGE 
```
ldb stage [-f] [-t <workspace_folder>] <ds:name>
```

`STAGE` command creates an LDB workspace at a given `<workspace_folder>` for dataset `<ds:name>`. The destination folder is expected to be empty. If LDB repository has no dataset `<ds:name>`, a new dataset is created. If `<ds:name>` references an existing dataset, it is staged out (but not automaticlly instantiated).

If workspace is not empty, `STAGE` checks if it holds a clean dataset, and clobbers it.  If `<workspace_folder>` holds a dirty dataset, a warning and a status of this dataset are printed before failure. If `<workspace_folder>` is not empty but does not hold an LDB dataset, a reminder to use `--force` is printed. 

*Use case:* 

```
$ ldb stage ds:cats
$ ldb status
 Dataset ds:cats, 0 objects, not saved in LDB.
```

If `STAGE` cannot locate an active LDB instance, it assumes a QuickStart, and proceeds with setting a new LDB instance (see QuickStart discussion).

## flags

`-f` or  `--force` 

allows to clobber the workspace regardless of what is there.


# INDEX 
```
ldb index [-m <format>] [--add-tags <tags>]
          [--annotation-update <strategy>] [-p <key>=<value>]
          <path> [<path> ...]
```

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

`--format <format>` - options: `{auto,auto-detect,strict,strict-pairs,bare,bare-pairs,infer,tensorflow-inferred,annot,annotation-only}` -  sets schema for data objects and annotations. `INDEX` fails if URI is not conformant with schema. `auto-detect` is the default. Some of these are simply short aliases for longer format names.

`--add-tags <tags>` Comma-separated list of tags to add to indexed data objects.

`--annotation-update <strategy>` Merge strategy for combining a data object's current annotation with the one discovered during indexing. Choices: `{merge,replace}` (default: `replace`)
 * `replace` will simply replace the old annotation with the new.
 * `merge` will merge top-level json keys if both the old and new annotations contain top-level JSON objects. Otherwise the new annotation will be used as with the `replace` option.

`-p <key>=<value>`, `--param <key>=<value>` Format-specific option. May be used multiple times. Different formats support different options. The following are supported:
 * `infer`
   * `base-label=<str>` - the label to be used for data objects that are inside of the base directory
   * `label-key=<str>` - a jmespath key expression indicating which key the inferred label should be stored under. The default when this option is not used is `label`.
 * `annot`
   * `single-file={true,false}` -  If `true`, instantiate all annotation JSON objects in a top-level array, creating a single JSON file called `dataset.json`. If `false`, instantiate each annotation in a separate JSON file. The default behavior if this param is not used is the same as setting it to `false`.

`--ephemeral-remote` - Allow non-storage cloud files to be indexed. They will be copied to read-add storage. Normally files outside of the local filesystem must be inside of a storage location unless the config value, `core.read_any_cloud_location = true` is set, but local non-storage (ephemeral) files may be indexed by copying them to a configured read-add location. This allows remote files to be treated the same way as local ephemeral files, and copied to read-add storage if necessary.

## formats

Brief format descriptions (see longer discussion of formats [here](formats.md))
 * `auto`, `auto-detect` - Auto-detect the data format. Supports detection of: `strict-pairs`, `annotation-only`, `tensorflow-inferred`
 * `strict`, `strict-pairs` - Only complete pairs of files will be indexed. The annotation file in each pair must have a name ending with `.json` and contain valid json. The data object file must have the same file name but with a different extension, and it must be in the same directory as the annotation file.
 * `bare`, `bare-pairs` - File pairs are detected as with `strict-pairs`, but bare data objects (without corresponding annotation files) are indexed too. Any file whose name does not end with `.json` will be considered a data object file.
 * `infer`, `tensorflow-inferred` - Annotation files will be generated containing labels that are inferred from each data object file's directory. This is based on the `labels="inferred"` option in TensorFlow's [`tf.keras.utils.image_dataset_from_directory`](https://www.tensorflow.org/api_docs/python/tf/keras/utils/image_dataset_from_directory). All files should be data object files that do **not** end with `.json`. The name of the directory passed to `ldb index` will be used as the label for data objects contained directly inside of it. Data objects within subdirectories will have nested labels. For example, if you called `ldb index --format tensorflow-inferred ~/data/animals/cat`, then `~/data/animals/cat/0001.png` would have the annotation `{"label": "cat"}` and `~/data/animals/cat/tabby/0001.png` would have the annotation `{"label": {"cat": "tabby"}}`. This would allow for query such as `ldb list --query label.cat.tabby`.  Note that for successful conversion of a label from another format into `tensorflow-inferred`, it must have the "label" JSON key and will fail otherwise.
 * `annot`, `annotation-only` - Only annotation files ending with `.json` may exist under the given location. Each annotation file must contain a JSON object with the key `ldb_meta.data_object_id` pointing to a data object hash. This hash must specify a data object that already exists in LDB. This JSON object must also contain an `annotation` key whose value will be used as the annotation for the specified data object. For example, some `.json` file may contain:
```
{
  "annotation": {
    "label": 1
  }
  "ldb_meta": {
    "data_object_id": "2c4a9d28cc2ce780d17bea08d45d33b3"
  }
}
```
This results in ldb using the following as the annotation for data object `id:2c4a9d28cc2ce780d17bea08d45d33b3`:
```
{
  "label": 1
}
```

# ADD  
```
ldb add <object-list> [<filters>]
```

Where,
* `object-list` can be of one object identifier types: `id:<hashsum>` | `object_path` | `ds:<name>[.v<num>]` | `workspace_folder`

`ADD` is the main workhorse of LDB as it allows data sample(s) to be added to a dataset staged in the workspace. 

`ADD` builds a list of objects referenced by their hashsum, storage location, or source dataset, and applies optional filters to this list. Objects passing the filters are merged into the currently staged dataset. When a data object is added to the workspace, an associated annotation may go with it. The particular annotation version will be determined by the source identifier. **In case of version collisions** (same object referenced multiple times with divergent annotation versions), **the latest annotation will be kept**. For instance, if `ds:cats` and `ds:small-cats` contain some of the same data objects but with different annotation versions, then `ldb add ds:cats ds:small-cats` would need to choose an annotation version for each common data object.

`ADD` allows for multiple objects (or object sets) of one type to be specified in one command. If no explicit object sources are provided and a filter option such as `--query` or `--file` is used, `ADD` assumes the source to be `ds:root` – which is all objects indexed by LDB with the most recently indexed annotation for each.

While `ADD` normally references sources already known to LDB (pre-indexed objects with valid identifiers), it can also target a storage folder directly. If all data objects in the folder have been indexed by LDB before, then no new indexing occurs. If some data objects have not been indexed, then LDB will index them if the config option `core.auto_index = true` is set. Otherwise an error will occur.

A special scenario for `ADD` arises when it targets ephemeral filesystem paths (anything outside the configured storage locations). Most commonly, such targets would be in the current workspace (where new objects were added directly, or where annotations were edited in-place). `ADD` can understand such changes and will save new data objects into permanent storage (see the `--read-add` option in `ADD-STORAGE`).

## object identifiers supported by `ADD`

1. `id:<hashsum>` - full hashsum of an object. Currently LDB uses MD5, so any MD5 hashsum that corresponds to an object indexed by LDB is a valid identifier.

*Use case:* 
```
$ ldb stage ds:cats
$ ldb add id:456FED id:5656FED    # result: objects with hashum ids 456FED and 5656FED added to dataset
```

2. `object_path` - any fully qualified (down to an object), or folder path within registered storage locations. Shell GLOB patterns are supported.

By default, `ADD` checks if the specified objects (or a list of objects recursively found in folder) were previously indexed by LDB, and uses the indexed annotations if this is the case. If some objects in the list are not found in index, `ADD` command fails with a reminder to run `INDEX` first.

*Use case:*
```
$ ldb stage ds:cats
$ ldb add gs://my-datasets/cats/black-cats/  # previously indexed location
  12 objects added to workspace (ds:cats)
```


*Use case:*
```
$ ldb stage ds:cats
$ ldb add gs://my-datasets/cats/white-cats/  # location is registered but folder contains new data
  error: 23 objects detected that are not found in ds:root
  Please run INDEX command first to process this storage location
```

This behavior can be altered with `auto-index` option in LDB configuration file. If set, this option allows `ADD` to implicitly `INDEX` to process objects in the folder or paths. This implicit call to `INDEX` assumes the objects are in the default format (one annotation file per each data objects), and will fail otherwise.

*Use case:*
```
$ ldb stage ds:cats
$ ldb add gs://my-datasets/cats/white-cats/  # location is registered but folder contains new data
  indexing gs://my-datasets/cats/white-cats/
  23 objects found, 20 new objects added to index, 3 annotations updated
  23 objects added to workspace (ds:cats)
```

3. `object_path` - any valid *fs* path NOT registered with `ADD-STORAGE`. The path can be fully qualified (down to objects), or reference a folder. When `ADD` is called on unregistered fs path, it expects annotations in default format and works in the following way:

  * If `object_path` is the workspace:
      -  `ADD` will process updated annotations even in absense of paired data objects (see `INSTANTIATE --annotations-only`)
      -  `ADD` will ignore data object transforms (see `TRANSFORM`)

  * In all other cases:
      - If previously indexed data objects are found, they are added to staged dataset, alongside with their annotations
      - If new objects (unknown to LDB) are found and `read-add` storage option configured, those objects are copied to `read-add` storage, indexed, and then added.
      - If new objects (unknown to LDB) are found but no `read-add` storage configured, `ADD` command fails.

*Use case:*
```
$ ldb stage ds:cats
$ ldb instantiate --annotations-only
$ sed -i 's/class=cat/class=dog/g' cat1.json 
$ ldb add .                  # result: annotation for cat1.jpg got a new version in LDB, and in ds:cats
```

*Use case:*
```
$ ldb stage ds:cats
$ cp ~/storage/cat1.jpg ./   # bring some object already in LDB but not in this dataset
$ ldb add ./cat1.jpg         # result: staged dataset ds:cats now includes cat1.jpg
```

*Use case:*
```
$ ldb stage ds:cats
$ cp ~/Downloads/cat1.jpg ./  # this object is not in LDB and read-add storage location configured
$ ldb add .                  # result: cat1.jpg copied to read-add storage, and then added
```



4. `ds:<name>[.v<num>]` - dataset name with an optional version number. Any valid LDB dataset can serve as a source of objects. Note that every dataset has objects paired with a particular annotation number, so it is possible to build a list where the same object is referenced several times with different annotations. If this is the case, the collision is resolved by using the latest annotation version among references.

*Use case:*
```
$ ldb stage ds:cats
$ ldb add ds:black_cats ds:white_cats.v2  # merged with latest ds:black_cats and v.2 of ds:white_cats
```

5. `ws:workspace_folder` - ADD can take a workspace folder name as an argument. This helps to avoid saving temporary datasets to LDB. 

*Use case:*
```
$ mkdir red_cats; cd red_cats
$ ldb stage ds:red_cats                        # create some temporary dataset 
$ ldb add ds:cats --query 'cat_color == `red`'    # fill it from some source
$ cd .. ; mkdir green_cats; cd green_cats         # create another dataset 
$ ldb stage ds:red_cats                        # create another temporary dataset
$ ldb add ds:cats --query 'cat_color == `green`'  # fill it from another source
$ cd ..  
$ ldb stage ds:red_and_green_cats              # make a permanent dataset
$ ldb add ws:./red_cats ws:./green_cats           # merge two temporary datasets into it 
$ ldb commit                                      # save a permanent dataset
$ rm -rf green_cats/ red_cats/                    # delete temporary datasets

```

ADD with a `workspace_folder` argument can also be used to share datasets between different LDB instances. In this latter case, the only requirement is to ensure that destination LDB instance has access to all file paths of the source workspace.

## filters and modifiers supported by `ADD`

`ADD` can be called with several filter and modifier flags. If multiple flags are specified, filters will be pipelined, so their order may matter. Multiple instances of one flag are not permitted in one `ADD` command.


`--file <query>`

Builds a query (see [LDB Query Syntax](./LDB-queries.md)) using fixed JSON fields specific to LDB index. The full list of field can be seen with `ldb eval  --file '@'`. The partial list as follows:

* fs.mtime - data object modification time. 
* last.indexed - annotation last indexing time. Affected by re-indexing (annotations are mutable).
* fs.size - data object file size in bytes.
* fs.path - data object path. If same data object was indexed under multiple paths, will match the last one.

Regular JMESPATH functions can be used to enrich the query.

*Use case:*
```
$ ldb add --file 'regex(fs.path, `gs:datasets/cat-bucket/.*`)'  # Object source is implicitly ds:root, path filtered by regex
```

`--path <regex expression>`

A convenience alias for ``` --file 'regex(fs.path, `regex expression`)' ```

`--query <query>`

Permits a query (see [LDB Query Syntax](./LDB-queries.md)) that references arbitrary JSON fields present in object annotation.

*Use case:*
```
$ ldb add --query 'class == `cats`'
```

`--pipe <exec> [<exec ...]`

Passes a list of objects through external program (e.g. an ML model) that filters or sorts them according to match criteria. Often used with `--limit`. LDB can be installed with two ready-made ML plugins (clip and resnet), but more custom plugins can be added. See the Pipe Plugins section below.

*Use case:*
```
$ ldb add --pipe clip-text 'cat sitting on a chair' --limit 100 # returns 100 images that best match the provided semantic embedding
```

`--limit <n>`

Cuts the input list of objects at \<n\> samples.

`--sample <probability>`

Passes every object in input list with a given Bernoulli probability.

```
$ ldb add ds:cats --sample 0.9 
```

`--tag <tags>`

Comma-separated list of tags. Select only data objects that contain at least one.

For example, the following are all equivalent:
```
ldb list --tag a,b --tag c
ldb list --file "contains(tags, 'a') || contains(tags, 'b')" --file "contains(tags, 'c')"
ldb list --file "contains_any(tags, ['a', 'b']) && contains(tags, 'c')"
```

`--no-tag <tags>`

Comma-separated list of tags. Select only data objects where at least one of these tags is missing.

For example, the following are equivalent:
```
ldb list --no-tag a,b --no-tag c
ldb list --file "! contains(tags, 'a') || ! contains(tags, 'b')" --file "! contains(tags, 'c')"
ldb list --file "! contains_all(tags, ['a', 'b']) && ! contains(tags, 'c')"
```

## Pipe Plugins

The `--pipe` option for LDB dataset commands `list`, `eval`, `add`, `del` takes one or more arguments which will be called as a subprocesses. The first argument should be the name of some script or executable which filters or sorts the dataset members passed to it. If this is only a name rather than a path, the first place LDB looks is in the `custom_code/ldb_user_filters/` directory within an ldb instance. By default this would be:
```
~/.ldb/private_instance/custom_code/ldb_user_filters/
```
Any executable available by name or path may be used. This internal directory is simply a place to isolate scripts from the rest of your environment if you wish.

If multiple arguments are given to `--pipe`, they are all called together as a single command. Flags or options (arguments beginning with `-`) should be avoided as they will collide with LDB's options. Complex commands may be wrapped in a script, so that only positional arguments are needed.

Because datasets are unordered collections, an ordering or sorting operation is most useful when combined with a following filter operation such as `--limit`.

A script intended for use by `--pipe` should expect a json array via stdin where each item is three element array in the form `[data_object_hash, data_object_path, annotation_path]`. LDB will instantiate the dataset in a temporary location, so the data object and annotation paths will point to files in this location. The script should then provide its filtered results as a series of data object hashes separated by new lines. This could be any type of sort or filter operation.

Here is a simple example of a python script that reverses the order of items in a dataset:

```python3
import json
import sys

if __name__ == "__main__":
    for data_object_hash, *_ in reversed(json.loads(sys.stdin.read())):
        print(data_object_hash, flush=True)
```

Scripts should be created and called the same way they would be called on the commandline. For example a python script like the one above could be run the following ways:

#### Platform independent

Place python code in `reverse.py` and call with `python3 path/to/reverse.py`. The disadvantage of this method is that you have to specify the path to `reverse.py`.

Example usage:
```
ldb add --pipe python3 path/to/reverse.py --limit 10
```

#### Unix

On Linux, MacOS, or other unix-like systems, simply put the python code in `reverse` with a shebang at the top:
```
#!/usr/bin/env python3
```
Make sure `reverse` is executable (`chmod +x reverse` or `chmod u+x reverse`). Then use the path to `reverse`, make sure `reverse` is on your `$PATH`, or place `reverse` in the ldb instance's plugin directory:
```
mv reverse ~/.ldb/private_instance/custom_code/ldb_user_filters/
```
Example usage:
```
ldb add --pipe reverse --limit 10
```

#### Windows

To run the python script with a single command, put the code in `reverse.py`, and create a batch file, `reverse.bat` in the same directory with:
```
@echo off
python3 "%~dp0\reverse.py"
```

Then use the full path of `reverse.bat`, make sure `reverse.bat` is in a location where it can be called, or place both `reverse.py` and `reverse.bat` in the ldb instance's plugin directory.
```
ldb add --pipe reverse --limit 10
```
Example usage:
```
ldb add --pipe reverse --limit 10
```

#### Plugin script examples

For `--pipe` plugin examples, see [pipe-plugins](../pipe-plugins). Copy the files in here to the ldb instance's plugin directory to make `reverse` available on Unix-like or Windows environments.

For `--apply` plugin examples, see [apply-plugins](../apply-plugins).


## LDB Query Language

Ability to construct complex queries is on of key features of LDB that permits it to extract data objects that are best suitable for training. LDB uses [JMESPath](https://jmespath.org) and supports JSON slices, projections, and reductions. This means, for example, that ML engineer can request only images with a given number of a particular class object detected.

Examples of LDB queries:

```
classes[0:1] == `["cats", "dogs"]`
```

```
( ! regex(classes[0], `cat.*` ) && length(classes) < `5`
```
More query examples are given [here](LDB-queries.md)

### LDB-provided Custom Query Functions

LDB provides a number of custom JMESPath functions. These are specified below with a signature in the format used by the [JMESPath spec documentation](https://jmespath.org/specification.html#built-in-functions):
```
return_type function_name(type $argname)
```

Regex functions:

These use the Python standard library's `re` module internally.

**regex**
```
bool regex(string $input_str, string $pattern)
```
Returns a boolean indicating whether or not `$input_str` matches `$pattern`.

**regex_match**
```
string|null regex_match(string $input_str, string $pattern)
```
Returns a string containing the matched group if `$input_str` matches `$pattern` and `null` otherwise.

Math functions:
Each of the following takes two arguments, which may be either a one-dimension array of numbers (vector) or a single number and applies a binary operator. If both arguments are an array, then the operation is applied element-wise. If at least one argument is an array, then an array is returned.

**add**, **sub**, **mul**, **div**
```
array|number add(array|number $x1, array|number $x2)
array|number sub(array|number $x1, array|number $x2)
array|number mul(array|number $x1, array|number $x2)
array|number div(array|number $x1, array|number $x2)
```

**neg**
```
array|number neg(array|number $x)
```
Returns the negation of the given number or each number in the given array.


### User-defined Custom Query Functions

Additional custom JMESPath functions may be added by placing a Python file in the `custom_code/ldb_user_functions/` directory within an ldb instance. By default, this would be:
```
~/.ldb/private_instance/custom_code/ldb_user_functions/
```
Any dependencies that this file relies on should be supplied by the user in this directory as well, so it is generally best to only use the Python standard library. In order to register your custom functions, at least one of the Python files in this directory must contain a `CUSTOM_FUNCTIONS` variable with a mapping (`dict`) of function names to a two-element tuple. The first tuple element should be the function and the second, should be a list of acceptable json types for each argument. If an argument accepts more than one type, they should separated by a vertical bar (`|`). For example if you didn't want to use the `add` function provided by LDB, you could create functions `add_nums`, `add_arrays` by creating a file `~/.ldb/private_instance/custom_code/ldb_user_functions/math_funcs.py` with the following:
```
def add_nums(x1, x2):
    return x1 + x2


def add_arrays(a1, a2):
    return [x1 + x2 for x1, x2 in zip(a1, a2)]


CUSTOM_FUNCTIONS = {
    "add_nums": (add_nums, ["number", "number"]),
    "add_arrays": (add_arrays, ["array", "array"]),
}
```
For an argument that could be a number or array, you would use `"array|number"` instead of just `"number"`.

# DEL 

```
ldb del <object-list> [<filters>]
```

`DEL` takes the same arguments and filters as `ADD`, but instead of adding the filtered objects it subtracts them from dataset staged in the workspace. If objects provided to `DEL` are not in the dataset, `DEL` does nothing.

# TAG 

```
ldb tag <object-list> [<filters>]
```

`TAG` is a text string in the ANSI character set `[0-9A-z_-]`. Multiple tags can be attached to data objects. Tags attached to objects are global – which means they apply to all instances of an object in all datasets irrespective of their annotations.

`TAG` takes the same arguments and filters as `ADD` command to identify datasets or individual objects to apply tags.

## flags 

`-a <tags>`, `--add <tags>`

Comma-separated list of tags to add to data objects

`-r <tags>`, `--remove <tags>`

Comma-separated list of tags to remove from data

# SYNC 
```
ldb sync [<object-list>] [<filters>]
```

`SYNC` synchronizes workspace state with the given `<object-list>`. If no arguments are given, the current working directory is used. It acts as a combination of `ADD` and `DEL` commands.

_Use case:_
```
$ ldb instantiate        # instantiate the workspace dataset
$ rm cats1.jpg           # delete one object file
$ ldb sync               # pick up changes in workspace
```

# TRANSFORM 
```
ldb transform <object-list> [<filters>]
              [-a <transforms>] [-r <transforms>] [-s <transforms>]
``` 

Add, remove, or set transforms for data objects within a dataset. Transforms are commands that will be run for each data object they are assigned to during instantiation as the final step when using `bare-pairs` (the default) or `strict-pairs` formats. Each transform will be given a temporary path for the data object and annotation, as well as an output directory, and the transform is responsible for writing it's output to the output directory. This may be used to generate any number of augment data objects or modified annotations during instantiation.

This command takes the same query arguments as the `ADD` command.

## flags

```
  -a <transforms>, --add <transforms>
                        Comma-separated set of transform names to add
  -r <transforms>, --remove <transforms>
                        Comma-separated set of transform names to remove if
                        present
  -s <transforms>, --set <transforms>
                        Comma-separated set of transform names to assign. A
                        matching data object's entire transform set will be
                        replaced with this one
```

## configuration

In order to assign transforms to a dataset you must configure a name for each transform. This may be done by creating a `transform.<name>` section with a `run` key in your ldb instance's `config` directory (`~/.ldb/private_instance/config` for the default instance). The `run` key should be set to command (possibly with arguments) in the form of an array. The command should be available on your system's `$PATH` as an executable, or it should be an absolute path. For example, you may have an executable `rotate-image` available which takes the number of degrees as an argument and writes a rotated version of the input image. You could configure different rotation transforms by adding the following to you `config`:
```toml
[transform.rotate-90]
run = ["rotate-image", "90"]

[transform.rotate-180]
run = ["rotate-image", "180"]
```
Then you can assign these transforms to data objects in a working dataset by running:
```
ldb transform -a rotate-90,rotate-180
```
Note that the default set of transforms contains a single item, `self`, which refers to a builtin transform that executes raw instantiation. This means that the original data object and annotation are simply copied to the target directory during instantiation. If the original data object and annotation are not wanted, then the `self` transform may be removed with:
```
ldb transform -r self
```
Instead of adding and removing to existing sets of transforms, the exact set of transforms to use may be specified with the `-s` or `--set` option:
```
ldb transform -s rotate-90,rotate-180
```

`-a` and `-r` may be used together in the same transform command, but `-s` may not be used with either `-a` or `-r`.

Query options or data object identifiers may be used to filter down the list of data objects updated:
```
ldb transform ds:other-dataset --query 'label == `cats`' --limit 10
```
If none are given then the update applies to every data object in the dataset.

The `LIST` command will show a `Transforms` column with the comma-separated names of transforms assigned to each data object in the dataset.

For a simple example, see [transforms/rotate.py](../transforms/rotate.py). An example config for this script:
```toml
[transform.rotate-90]
run = ["python3", "path/to/transforms/rotate.py", "90"]

[transform.rotate-180]
run = ["python3", "path/to/transforms/rotate.py", "180"]

[transform.rotate-45-n45]
run = ["python3", "path/to/transforms/rotate.py", "45", "-45"]
```

## Replacing transforms

In LDB, a transform assigned to a data object is an actual command (e.g. `["rotate-image", "90"]`) saved as an immutable object. The configured name for a transform (e.g. `rotate-90`) is simply an identifier, providing an easy way to refer to a particular command. This means that renaming transforms in your config file is perfectly fine. However, new commands should receive new config entries.

For example, changing `[transform.rotate-90]` to `[transform.rotate-image-90]` without changing the array under `run` allows you to refer to the same transform with a new name, `rotate-image-90`. The `LIST` command's output will automatically reflect this change. However, if you want to modify the command assigned to some data objects, you should add a new config entry for the new command. The use `TRANSFORM` command's `-a` and `-r` options to add/remove transforms.

Note that this also means that transform config entries should generally only be removed if they are not assigned to any data objects in any dataset. If an assigned transform is deleted (or the array under `run` is modified), then `LIST` will refer to the unnamed transform with a hash identifier, until you add a name for the original command. You may also use this hash in place of the transform's name with the `TRANSFORM` command's `-a`, `-r`, and `-s` options.

# INSTANTIATE 
```
ldb instantiate [<object-list>] [<filters>]
                [--pipe <exec> [<exec> ...]] [-m <format>]
        	[-f] [-t <dir>] [--apply <exec> [<exec> ...]]
                [-p <key>=<value>]
```

`INSTANTIATE` partially or fully re-creates dataset in a workspace.  This command works whether the dataset in the workspace is committed (clean) or not (dirty). To partially reconstruct the dataset, `INSTANTIATE` can take any valid object ids - hashsums or full object paths (only those objects are instantiated). If a sub-folder is provided, instantiation happens in this sub-folder, which is created if needed.

## flags

`-p <key>=<value>`, `--param <key>=<value>` Format-specific option. May be used multiple times. Different formats support different options. The following are supported:
 * `infer`
   * `base-label=<str>` - a single label to be instantiated in the base directory instead of a subdirectory. Provides a way to mirror the same option on the `index` command.
   * `label-key=<str>` - a jmespath key expression indicating which key the inferred label should be stored under. The default when this option is not used is `label`.

`--apply <exec> [<exec> ...]`

An executable, along with any arguments that it should take, which should apply the final instantiation step. This is useful for making inferences or appling other transformations during instantiation.

LDB will change the working directory to the executable's parent directory before calling it as a subprocess in order to make it easy for the executable to reference any relevant artifacts (i.e. ML models or data) with relative paths.

LDB will first instantiate data objects and annotations normally in a temporary directory. A two-member json array will be passed to this executable, containing first the temporary directory and second the final directory the executable should write to. For example, the executable would receive something like this:
```json
["/home/user/workspace-dir/.ldb_workspace/tmp/tmplole6mzj", "/home/user/workspace-dir"]
```
Then the executable should read files from the first directory, and write results to the second directory. This allows the executable to transform data objects or annotations in any way. After the executable's process finishes, LDB will erase the temporary directory and any files remaining in it.

For a simple example see [apply-plugins/random_predictions.py](../apply-plugins/random_predictions.py). This script simply makes random predictions and adds them to a `"prediction"` key for each existing annotation.

For a more practical example, you can index a sample of textocr annotations. Then use [apply-plugins/textocr_crops.py](../apply-plugins/textocr_crops.py) to find text annotations matching a regex and generate cropped images based on their bounding boxes. In this example we look for annotations matching roman numerals in the range 1-10 (i.e. I-X):
```
ldb stage ds:roman-numerals
ldb index s3://ldb-public/remote/data-lakes/textocr/small/
ldb add --path '^ldb-public/remote/data-lakes/textocr/small/.*'
ldb instantiate --apply python3 path/to/apply-plugins/textocr_crops.py '(?i)^(V?I{1,3}|I?[VX])$'
```

Note: Because `--apply` can take any number of arguments, the positional path argument that `instantiate` can take should be before `--apply`:
```
ldb instantiate ./some/path --apply script arg1 arg2
```
Or alternatively, it may go after `--`, which indicates that all following arguments are positional:
```
ldb instantiate --apply script arg1 arg2 -- ./some/path
```
 
`--annotations`, `--annotations-only`

Only instantiates annotations (no data objects). Can be combined with `--format`.

`--format <format>` - choices: `{strict,strict-pairs,bare,bare-pairs,infer,tensorflow-inferred,annot,annotation-only}` -  sets schema for data objects and annotations. See `INDEX` for details about each format.

Specific annotation output format. The list of formats mirror those in `INDEX` command with `--format` flag.

`--preserve-paths`

Instantiate objects preserving full storage paths. Only supported for default LDB format (annotation file per every object).

# GET

```
ldb get <object-list> [<filters>]
        [--pipe <exec> [<exec> ...]] [-m <format>]
        [-t <dir>] [--apply <exec> [<exec> ...]] [-p <key>=<value>]
        [<path> [<path> ...]]
```

Add the specified data objects into a working dataset and instantiate them. 
This command works as a combination of several LDB operations and carries out the following steps:

- `stage` unnamed dataset in the target directory (if it is not already a valid workspace)
- `add` the data objects specified
- `instantiate` these data objects

Differences from running the `stage`, `add`, and `instantiate` commands separately are:
- If the directory is not already a workspace, then the newly staged working dataset will be given a temporary name. To save such a dataset you must provide a name when calling `commit`.
- The data object identifiers and query filters are run once and resolved to a logical dataset internally. Then `add` and `instantiate` are both run on this dataset. This avoids the overhead of resolving these specifiers multiple times, and ensures that non-deterministic options such as `--sample` do not result in different datasets for the `add` and `instantiate` operations.
- The `instantiate` command normally results in a full instantiation of all items in the working dataset, and ensures that no additional files exist in the workspace. Under the `get` command, the instantiation only applies to the data objects and specified by the command and does not remove additional files. This allows for partial and additive instantiations.

One use case is quickly obtaining a dataset for training:
```
ldb get ds:cats
```
Or the union of multiple datasets:
```
ldb get ds:dogs ds:cats
```

Since any dataset identifiers are allowed, this could also be a storage location:
```
ldb get s3://ldb-public/remote/data-lakes/dogs-and-cats/
```
Or filtered result:
```
ldb get s3://ldb-public/remote/data-lakes/dogs-and-cats/ --query 'inference.class == class' --limit 10
```

You may also wish to specify the target directory intead of using the current directory:
```
ldb get ds:cats -t cats
ldb get ds:dogs ds:cats -t dogs-and-cats
```

# COMMIT 
```
ldb commit [-m <message>] [--auto-pull [{True,False}]] [<dataset>]
```

`COMMIT` takes the currently staged dataset and saves it to LDB. This action renders workspace "clean" – meaning that all changes are saved, and workspace can be erased if needed. The result of `COMMIT` command on "dirty" workspace is always a new version of dataset.

The optional `message` flag will be added as the commit message and shown in `ldb status` when called with a dataset as an argument.

# DIFF 
```
ldb diff [-s] [<dataset>] [<dataset>]
```

`DIFF` prints a list of differences between two datasets. `DIFF` with one argument can only run from a workspace and uses as the first comparand.

## flags
```
  -s, --summary  Show only the number of additions, deletions and
                 modifications.
```

# LIST  
```
ldb list <object-list> [<filters>]
```

`LIST` can take the exact same arguments as `ADD` but only prints matching objects instead of actually adding them.
Unlike `ADD`, `LIST` without arguments targets objects in a staged dataset. To target objects in LDB index, use `ds:root` as the object source.

## flags

`-s` or  `--summary` 

just prints object counts

`-v` or  `--verbose`

detailed object information

# STATUS  
```
ldb status [<dataset>]
```

When run without arguments from a workspace, `STATUS` summarizes state of a staged dataset. This includes any uncomitted changes and current object counts. If called with an argument, `STATUS` prints a summary for a dataset in the argument.

# PULL 
```
ldb pull [<object-list>]
```

`PULL` changes annotation versions for indicated object(s) in workspace to latest known to LDB. If no `object-id(s)` specified, command will apply to all objects in a workspace. Pull action applied to objects not in the current workspace are ignored.

# DS
```
ldb ds list
ldb ds del <dataset> [<dataset> ...]
```

## DS LIST
```
ldb ds list
```

Lists latest versions of all datasets in LDB repository.

## DS DEL
```
ldb ds del <dataset> [<dataset> ...]
```

Deletes the given dataset entries. This command deletes all of the versions under a given dataset name, so arguments should not specify a version number. For example, use `ds:my-dataset` rather than `ds:my-dataset.v2`.

# EVAL
```
ldb eval <object-list> [<filters>] [<show>]
```
`EVAL` works the same way as `LIST`, except it will print out json results, for use in debugging queries for other commands such as `ADD` and `LIST`. The `--query` or `--jquery` options are used to filter annotations, and `--show` or `--jshow` are used to search within these annotations and print the search results. Note that `--query` and `--show` use the custom JMESPath-like expressions and `--jquery` and `--jshow` use fully-compliant JMESPath queries. In addition, the `--file` option is used to filter on file attributes, and `--file-show` is used to search within file attributes and print the search results. These filters can be can be used with other filter options, such as `--limit`, `--pipe`, or multiple `--query` options to filter items as well.

The `query` argument must be a valid JMESPath query to be run over annotations (if used with `--query` flag) and over data object file attributes (if used with `--file`). The `path` arguments may be any data object identifiers that the `ADD` command can take.

The `-j` or `--json-only` option will print only JSON query results. Without it, each JSON object is preceded by the corresponding data object hash.

It is also possible to provide multiple query filters and multiple search results to show, for example:
```
ldb eval ds:pets --query "type == 'image'" --query "format == 'png'" --show "subject" --show "confidence"
Output:
id:a4ae03f8db03dcb93dadc740260b9eb0
"cat"
0.7
id:f75eebabf9ece701641b3ffa7b73a021
"dog"
0.5
id:0890edfe5a1cc9c1fc3373f9afc4bac0
"cat"
0.9
```

# QUERY
```
ldb query [<filters>] <json-file-list>
```
The `query` command is used for querying unindexed or raw JSON files, to test out queries / JMESPath selections. It can be used with supplied JSON files on the command line, where `--query` or `--jquery` will be used to filter files, and `--show` or `--jshow` will be used to search within these files and print the search results. Note that `--query` and `--show` use the custom JMESPath-like expressions and `--jquery` and `--jshow` use fully-compliant JMESPath queries.

For example:
```
ldb query --query "type == 'image'" --show "subject" test1.json test2.json
Output:
"cat"
"dog"
```

The `query` command can also read JSON data from stdin if no files are specified, for use with piping from other command-line programs:
```
cat test1.json | ldb query --query "type == 'image'" --show "subject"
Output:
"cat"
```

In addition, there are two options for combining and uncombining input JSON files: `--slurp` combines the supplied files into a top-level array before running the query filters and showing search results. `--unslurp` uncombines a supplied top-level array into individual JSON files before running the query filters and showing search results. Unslurp is particularly useful for stdin input, as a top-level array of all files can be passed into stdin, then split with `--unslurp`, for example:
```
echo '[{"A":1,"B":50},{"A":2,"B":100}]' | ldb query --unslurp --query 'A == `2`' --show 'B'
Output:
100
```

Both slurp and unslurp can be used together to transform individual files with top-level arrays into one top-level array, described conceptually as:
```
[A, B, C], [D, E, F] -> [A, B, C, D, E, F]
```

As well, similar to the `eval` command, the `query` command has selectable indentation for JSON output (if the show selection returns JSON as a search result).

# UNINDEX

```
ldb unindex <object-list> [<filters>]
```

`UNINDEX` takes the same arguments and filters as `DEL` and permanently removes the data object entries from the index. This requires the data objects given not to be members of any saved datasets. Otherwise an error will be thrown. To delete datasets that are no longer useful, see the `ldb ds del` command.

# COMPLETION
```
ldb completion [-h] [-q | -v] [-s {bash,zsh,tcsh}]
```
To add tab-completion for a particular shell, save the output of this command into a file in your shell's completion directory. Use the `-s` option to specify your shell. For example, on a Linux machine, adding bash completion might be:
```
ldb completion -s bash | sudo tee /usr/share/bash-completion/completions/ldb
```
And adding zsh completion might be:
```
ldb completion -s zsh | sudo tee /usr/local/share/zsh/site-functions/_ldb
```

The exact location of each shell's completion directory varies from system to system.
