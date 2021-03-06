## Metadata and annotation formats

LDB stores, searches and versions metadata and annotations in JSON. LDB does not dictate any specific schema, and just needs to understand how specific data objects (e.g. `cat1.png`) are related to information that describes it (e.g. `cat1.json`, or some JSON array that references `cat1.png`). Different *brand-name* dataset formats may employ incompatible ways to encode this relation, so LDB commands like INDEX and INSTANTIATE might need an explicit argument to specify a format under the `--format` flag.

Here is what is supported so far:

* `auto | auto-detect` – auto-detected data format. Supports detection of: `strict-pairs`, `annotation-only`, `tensorflow-inferred`

* `strict | strict-pairs` – "native" LDB format that assumes data and metadata come in pairs of files (object + json). The annotation file in each pair must have a name ending with `.json`. The data object files are matched to their annotations by means of sharing filenames (e.g. `cat1.json` + `cat1.jpg`), and pairs must reside in the same directory. LDB does not provide restrictions on the actual JSON schema and will accept any valid JSON content.

* `bare | bare-pairs` – complete pairs are detected as with `strict-pairs`, but bare data objects (data without annotation files) are also indexed (any file whose name does not end with `.json` will be considered a data object). This format is the primary way to index un-annotated data. 

* `infer, tensorflow-inferred` – label-only format based on the `labels="inferred"` option in TensorFlow's [tf.keras.utils.image_dataset_from_directory](https://www.tensorflow.org/api_docs/python/tf/keras/utils/image_dataset_from_directory)  method. Files supplied in this format must have names that do not end with `.json`. The name of the directory passed to INDEX is used as the label for all data objects inside, and objects within subdirectories will have nested labels. 
 
    For example, a call `ldb index --format tensorflow-inferred ~/data/animals/cat/`, would result in object at path `~/data/animals/cat/0001.png` having the annotation `{"label": "cat"}`, and object at path `~/data/animals/cat/tabby/0001.png` having the nested annotation `{"label": {"cat": "tabby"}}`, and so on. Note that for successful conversion of a label from another format into the tensorflow-inferred, it must have the "label" JSON key and will fail otherwise.

* `annot | annotation-only` - this format targets labeling teams and allows to pass modified annotatons back and forth without the attached data objects. 

  It therefore assumes that data objects were already indexed by LDB, and folder in `annotation-only` format only has new annotations in .json files. To match these annotations to entries in LDB index, they must contain a JSON object with the key `ldb_meta.data_object_id` pointing to hashsum. This hash must match some data object already known to LDB index. The actual annotation is stored under the "annotation" key, for example:

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
  This results in ldb indexing the following annotation for data object `id:2c4a9d28cc2ce780d17bea08d45d33b3`:

  ```
  {
    "label": 1
  }
  ```
* `label-studio` - This handles exports from a Label Studio instance in the [JSON format](https://labelstud.io/guide/export.html#JSON). Each export should be a single JSON file containing a top-level array of JSON objects following Label Studio's [raw JSON format](https://labelstud.io/guide/export.html#Label-Studio-JSON-format-of-annotated-tasks). LDB will treat each JSON object in this top-level array as an annotation.

  Under Label Studio's JSON format, [certain keys](https://labelstud.io/guide/export.html#Relevant-JSON-property-descriptions) are expected to be present, including a `data` key with information about the labeling task. LDB will populate some data under `data.data-object-info`, if it doesn't already exist. In particular, LDB will make sure the following fields exist:
  * `data.data-object-info.path_key` - The key of the data object's URI. Usually a sub-key of `data`, such as `data.image`. This can be inferred by LDB if there is only one key under `data` aside from `data-object-info`. If present, LDB will use the existing value. LDB needs the URI of the data object in order to index it if it hasn't already been indexed by LDB.
  * `data.data-object-info.md5` - The MD5 hash of the data object. If this key is already present, and the hash matches a data object LDB has indexed previously, then LDB does not need to index this annotation's data object.

  These fields allows Label Studio tasks to be passed between LDB and Label Studio instances repeatedly while maintaining consistent data object identifiers and avoiding repeated indexing of the same data objects. In order to export data from LDB that was indexed using the `label-studio` format, stage it as a working dataset and run:
  ```
  ldb instantiate --format label-studio
  ```
  This will generate a single `annotations.json` file which you can then [import into a Label Studio instance](https://labelstud.io/guide/tasks.html#How-to-import-your-data).


TODO

* `annotation-only` format extension that serves http/https
  * "path" key in "ldb_meta" object of 'annotation-only' to specify an object location
  * top-level array in 'annotation-only' to describe multiple files
* COCO 
* Google ImageNet
