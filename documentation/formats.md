Since LDB parses annotations, it has to understand the specific annotation formats. LDB supports several popular formats out of the box, which means it can index data in these formats, and instantiate them. Here is what is currently supported:

* `auto | auto-detect` - auto-detected data format. Supports detection of: `strict-pairs`, `annotation-only`, `tensorflow-inferred`

* `strict | strict-pairs` - this is the "native" LDB format that assumes data comes in pairs of files (json + object). The annotation file in each pair must have a name ending with `.json`. The data object files are matched to their annotations by means of sharing filenames (e.g. `cat1.json` + `cat1.jpg`), and pairs must reside in the same directory. LDB does not provide any restrictions on the actual JSON schema and will accept any valid JSON content.

* `bare | bare-pairs` - complete pairs are detected as with `strict-pairs`, but bare data objects (without annotation files) are also indexed (any file whose name does not end with .json will be considered a valid data object file). This format is the primary way to index un-annotated data. 

* `infer, tensorflow-inferred` - label-only format based on the `labels="inferred"` option in TensorFlow's `tf.keras.utils.image_dataset_from_directory` method. All files should be valid data objects with names that do not end with `.json`. The name of the directory passed to INDEX is used as the label for all data objects inside. Data objects within subdirectories will have nested labels. For example, if you called `ldb index --format tensorflow-inferred ~/data/animals/cat/`, then object at path `~/data/animals/cat/0001.png` would have the annotation `{"label": "cat"}` and object at path `~/data/animals/cat/tabby/0001.png` would have the nested annotation `{"label": {"cat": "tabby"}}` permitting a query such as ```ldb list --query 'label.cat == `tabby`'```, and so on. Note that for successful conversion of a label from another format into the tensorflow-inferred, it must have the "label" JSON key and will fail otherwise.

* `annot | annotation-only` - this format targets labeling teams and allows to pass modified annotatons back and forth without the attached data objects. 

It therefore assumes that data objects were already indexed by LDB, and folder in `annotation-only` format only has new annotations in .json files. To match these annotations to entries in LDB index, they must contain a JSON object with the key `ldb_meta.data_object_id` pointing to hashsum. This hash must match some data object already known to LDB index. The actual annotation is stored under the "annotation" key, for example:

```json
{
  "annotation": {
    "label": 1
  }
  "ldb_meta": {
    "data_object_id": "2c4a9d28cc2ce780d17bea08d45d33b3"
  }
}
```
This results in ldb indexing the following annotation for data object id:2c4a9d28cc2ce780d17bea08d45d33b3:
```
{
  "label": 1
}
```

TODO

* label-studio format
* group description format that stores paths to objects
