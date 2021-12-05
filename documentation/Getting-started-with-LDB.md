# LDB workflow

LDB is an MLOps tool that indexes the existing immutable storage for data files and allows for easy construction of datasets based on metadata queries. 
These datasets are meant to be used for model training, and are usually further updated based on the model performance (Data-driven AI loop).

A good example for the data-driven AI task can be derived from the [2021 competition](https://https-deeplearning-ai.github.io/data-centric-comp/) 
by [DeepLearning.AI](http://deeplearning.AI) to train a ResNet50 model to recognize hand-written roman numerals: 

![roman numerals dataset, courtesy DeepLearning.AI](/images/numerals-deeplearningAI.png)

A starter set of ~3,000 labeled training images is provided in competition, and contestants are free to add more (up to 10,000 images) to score on a leaderboard. The task aims at demonstrating how performance improvements can be achieved with managing data alone. 

To get the optimal performance on a sufficiently expressive deep learning network, one generally needs to overcome the following data-specific challenges:

* Cleanse data objects. Remove duplicates, irrelevant, or excessively noisy samples.
* Clean annotations. Make sure annotations match the content of data samples.
* Enrich the initial sample set. Find ways to obtain more data from the real world.
* Introduce augmentations to teach the network about data variations.
* Add effective synthetic samples (teacher-student, GAN, etc.) to cover any remaining data gaps.

At the level of organization, all these tasks can be reduced to manipulating the membership information in
(possibly overlapping) collections – such as original data samples, auxiliary samples, synthesized samples, transformed samples, and so on.

LDB simplifies dataset manipulation and version tracking by indexing unique data objects, 
constructing the datasets by querying object metadata, and versioning the results. 

To demonstrate a sample data-driven workflow in LDB, let us begin with holding starter data for the DeepLearningAI challenge. 
Assuming it is hosted at `gs://iterative/roman-numerals/` let us create a dataset called `"numerals"`:

| Step | Command |
| --- | --- |
| Start a new dataset in the workspace | `$ ldb stage ds:numerals` |
| Add objects from a given path | `$ ldb add gs://iterative/roman-numerals/` |


Now we have created a dataset `"numerals"` in our workspace and filled it with input references. LDB datasets are logical entities, so no data objects were copied or moved. Instead, LDB have read the files in the provided location, found all unique data samples (ignoring any duplicates), parsed their annotations and stored data pointers to the workspace. 

To use`"numerals"` dataset in subsequent steps of the workflow, let us save it to LDB:

| Step | Command |
| --- | --- |
| Save dataset "numerals" v.1 to LDB | `$ ldb commit` |

This action stores `"numerals"` into LDB repository, and assigns a version number to it.

The DeepLearningAI competition comes with a ResNet50 docker image for evaluation. One "quick and dirty" way to check for sanity of training data is to check if the network can generalize over the training set. To simulate the competition leaderboard, we provide a version of ResNet50 here:  [instructions for running](TODO).

Now let us assume ResNet50 was trained on the starter data, and for every training sample produced the following output in JSON format, where "class" is the input label, and "inference" is the output label:

```json
{
	"path": "./i/125d.jpg",
	"class": "i",
	"inference": {
			"class": "ii",
			"confidence": 0.2,
	},
}
```

These output annotations are available in a bucket `gs://iterative/inference/`.

As usual for inferences, we can observe that some training inputs were not generalized properly, or their confidence remained low. 
Some of these errors highlght the problems with data: the underlying objects could be noisy, incorrect, or paired with a wrong label.

To investigate further, let us isolate these errors.  
We can stage a new dataset and query annotations from inference to fill it with objects the network failed to train on:


| Step | Command |
| --- | --- |
| Start a new dataset  | `$ ldb stage ds:to-examine` |
| Add misclassified objects | `$ ldb add gs://iterative/inference/ --query class != inference.class` |


Now we have created a new dataset `"to-examine"` that holds references to data objects that we want to inspect. 
However, there are no files to examine in our workspace yet. This is because LDB datasets are logical entities that hold pointers, not actual data files. 
To instantiate this dataset (transfer all relevant objects from storage into workspace), we will use the INSTANTIATE command:

| Step | Command |
| --- | --- |
| Instantiate dataset in a workspace  | `$ ldb instantiate` |

For the sake of example, let's assume the dataset `"to-examine"` now holds ten annotated images, which may look somewhat like this: 

![Courtesy: DeepLearning.ai, subset of images compiled by Pierre-Louis Bescond.](/images/numerals-bescond.png)

Upon closer examination, we note that a second image in the top row is too noisy, and the third image in bottom row does not belong to a set. On the other hand, the very first image should have been easy to recognize (so maybe it carries the wrong annotation) – and so on. For now, let us try to delete these images from the training set and see if the network performs better.

To accomplish this task, we can save dataset `"to-examine"`, stage `"numerals"`, and subtract the former from the latter:


| Step | Command |
| --- | --- |
| Save "to-examine" dataset   | `$ ldb commit` |
| Stage "numerals" dataset | `$ ldb stage ds:numerals` |
| Subtract contents of a dataset| `$ ldb del ds:to-examine` |
| Save dataset "numerals" v.2 | `$ ldb commit` |

Once we have successfully modified the working dataset, and can instantiate it to re-train the model and check the performance. 

If we don't like the result and want to roll back the changes, LDB versioning system makes it easy. All we need to roll back to the previous dataset version is to stage it and push as a new revision:

| Step | Command |
| --- | --- |
| Stage a specific dataset version  | `$ ldb stage ds:numerals.v1` |
| Save it as the "current" version | `$ ldb commit` |

At this point, LDB holds two revisions of the dataset "numerals", v.1 and v.2, and the former is the version that will now be checked out by default.

Inference is not the only metric you can use to close the data-train loop. Obviously, a network may just memorize wrong labels and offer little guidance to training data via inferences. To collect more signals from training loop we can use metrics like learning gradients per sample, or result confidence:

| Step | Command |
| --- | --- |
| Check objects with low confidence | ``$ ldb list gs://iterative/inference/ --query 'inference.confidence < `0.55`'`` |

### Dataset merging and class balancing

Another key operation to data-driven AI is the dataset merging. LDB allows for dataset slicing, dicing and merging operations via a sequence of ADD and DEL commands paired with query filters. However, when merging two or more datasets, it is also important to also keep track of class balancing.

To that end, LDB supports `--limit ` and `--sample-ratio` arguments that collectively define the absolute and relative limits to a number of data objects being merged. For example, let us assume our roman numerals dataset underperforms for numeral `'i'`. To address this deficiency, we might want to boost it with more samples that we generated and stored in a dataset `generated-numerals`, up to a limit that would not upset our class balance:

| Step | Command |
| --- | --- |
| Fill workspace with desired class samples |   ``ldb add ds:generated-numerals --query 'class == `i`'  --limit 100`` |


### Isolating objects with helper ML models

So far, we saw how a dataset can be staged, instantiated, filled, evaluated, and modified.
Another key operation for model performance analysis is discovering training samples that would best represent the underperforming subclass.

For example, you may find that a particular class (say, numerals `'iii'`) is under-represented, and you want more of them. Let us also assume that you have a set of handwritten numerals to choose from, but they are not annotated. 

A classical solution to this problem is to run a helper model that would produce pre-annotations, and do the rest of annotation work manually. LDB simplifies this task by allowing a helper to be called within a query. LDB ships with several helper models (like CLIP embeddings and visual similarity), and more can be added:

| Step | Command |
| --- | --- |
| Add visually similar images to a working dataset  | `$ ldb add gs://iterative/handwritten --sort CLIP "iii" --limit 100` |


### Indexing storage locations

So far we have assumed that LDB parses data objects and annotations on the fly whenever a storage location is queried. 
There are several topics here that we need to cover to make our workflow more efficient.

As your data storage grows, parsing it repeatedly for every request becomes suboptimal. 

Repeated queries waste time, and coupling queries with storage locations is cumbersome. To solve this problem, LDB saves every data object and annotation it comes across into internal database (index). Index has a role of "root dataset" to which all data objects are assigned by default, and can be referenced as `ds:root`. Therefore, looking for a specific data object based on the previously indexed annotation (or user-defined tag) may look simply like this:

| Step | Command |
| --- | --- |
| List all objects matching annotation field in the index | ``$ ldb list ds:root --query 'class == `i`' `` |
| List all objects matching a tag in the index  | `$ ldb list ds:root --tag "training" `| 

Also note that LDB addresses data objects by hashsum, and therefore only keeps track of unique data samples. However, data objects are often coupled with annotations that may change over time and are not unique. This presents two additional problems: first, how to update an annotation, and second – how to ensure reproducibility in a dataset when annotations are a moving target?

To answer these challenges, LDB supports re-indexing and annotation versioning. 

Re-indexing asynchronously queries a specified storage path for changed data objects and annotations, and adds them to the index. When adding a new annotation, LDB also retains a previous version (if any). This ensures the datasets referencing previous annotations will remain reproducible:

| Step | Command |
| --- | --- |
| Reindex objects at a given location | `$ ldb index /storage/` |


### Modifying annotations in existing datasets

We have seen how annotations can be updated with re-indexing. Practically, this means that we can send our dataset annotations to a 3rd party labeling service, receive the corrected records, and re-index them in LDB. To continue our example, let us assume we have pre-annotated a part of `handwritten` dataset, and sent the rest to an annotation service. Upon receiving the results, we can simply re-index the target to pick the updates:

| Step | Command |
| --- | --- |
| List all objects matching annotation field in the index | `$ ldb index gs://iterative/handwritten-reannotated/` |

However, as we mentioned, this change would not affect the existing datasets that are referencing the older annotations. To upgrade all annotations in a dataset to the latest revision found in index, one can use PULL command:

| Step | Command |
| --- | --- |
| Bump annotations to the latest version | `$ ldb pull` |

Pull command also works for individual data objects (referenced by hashsum or object path). A reverse operation to pull would be to set a specific object to a specific version of annotation:

| Step | Command |
| --- | --- |
| Bump annotations to the latest version | `$ ldb add 0xFD45DE --label-version 2` |

Finally, it might be convenient to correct minor errors in annotations right from the workspace. This can be done with staging the dataset, editing annotations, and adding the workspace (as a whole, or by individual files) back into a dataset:

| Step | Command |
| --- | --- |
| Stage a dataset | `$ ldb stage ds:numerals` |
| Correct an annotation | `$ sed -i 's/"class": "i"/"class": "ii"/g' 125d.jpg` |
| Register the change | `$ ldb add .` |
| Push the change into LDB | `$ ldb commit` |

### Indexing data in various formats

The DeepLearningAI competition permits up to 10,000 training images, but only ships with a starter set of 3,000. A natural question for a data scientist working on this challenge is where to find more data. The good news is that nowadays just about every data class in the world exists in the public domain. The bad news is that public datasets come in different (and often incompatible) formats.

The primary method to pair data objects with annotations supported by LDB is matching-name JSON annotations within the same folder, for example:

- 154F.m4a, 154F.json,
- 23DE.m4a, 23DE.json,
...

Alternatively, LDB also understands the scheme where multiple data objects are described in a single JSON file residing at root folder:

- 154F.m4a,
- 23DE.m4a, 
- annotations.json

Both schemes permit arbitrary storage configurations, and double as default scheme for many labeling tools (such as [Label Studio](https://labelstud.io)).

However, a lot of "branded" datasets follow unique and proprietary conventions for annotations. For example, the DeepLearningAI competition on roman numerals encodes classes as folder names. Alternatively, COCO uses multiple shared JSON files to annotate objects in a dataset, while ImageNet combines a single key annotation file with class-specific folders.

LDB ships with a pre-processor for COCO, ImageNet, Google OpenImage, and general folder-class schemes. These can be selected during indexing with `--format` argument providing the format:

| Step | Command |
| --- | --- |
| Index objects in ImageNet folder | `$ ldb index --format ImageNet /storage/ImageNet500K/` |

Additional formats can be included by writing the custom pre-processors ([more on this here](TODO)).


