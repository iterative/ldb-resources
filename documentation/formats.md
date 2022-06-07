Since LDB parses annotations, it has to understand the specific annotation formats. LDB supports several popular formats out of the box, and allows for user-defined JSON formats as well.


auto, auto-detect - Auto-detect the data format. Supports detection of: strict-pairs, annotation-only, tensorflow-inferred

strict, strict-pairs - Complete pairs of files will be indexed. The annotation file in each pair must have a name ending with .json and contain valid json. The data object file must have the same file name but with a different extension, and it must be in the same directory as the annotation file. LDB does not provide any restrictions on actual JSON schema.

bare, bare-pairs - File pairs are detected as with strict-pairs, but bare data objects (without corresponding annotation files) are indexed too. Any file whose name does not end with .json will be considered a data object file.

infer, tensorflow-inferred - Annotation files will be generated containing labels that are inferred from each data object file's directory. This is based on the labels="inferred" option in TensorFlow's tf.keras.utils.image_dataset_from_directory. All files should be data object files that do not end with .json. The name of the directory passed to ldb index will be used as the label for data objects contained directly inside of it. Data objects within subdirectories will have nested labels. For example, if you called ldb index --format tensorflow-inferred ~/data/animals/cat, then ~/data/animals/cat/0001.png would have the annotation {"label": "cat"} and ~/data/animals/cat/tabby/0001.png would have the annotation {"label": {"cat": "tabby"}}. This would allow for query such as ldb list --query label.cat.tabby. Note that for successful conversion of a label from another format into tensorflow-inferred, it must have the "label" JSON key and will fail otherwise.

annot, annotation-only - Only annotation files ending with .json may exist under the given location. Each annotation file must contain a JSON object with the key ldb_meta.data_object_id pointing to a data object hash. This hash must specify a data object that already exists in LDB. This JSON object must also contain an annotation key whose value will be used as the annotation for the specified data object. For example, some .json file may contain:
