
`section under construction`

# Intro

LDB is an MLOps tool that indexes the existing immutable storage for data files and annotations for easy construction of datasets based on metadata queries. These datasets are meant to be used for model training, and are periodically updated based on the model performance (Data-driven AI loop).

### LDB workflow cycle:

0a. [Start ldb instance](command-summary.md#init) on a shared disk that everyone in the team has access to (step not needed for private instance)

0b. [Configure immutable storage locations](Command-summary.md#add-storage) and access privileges (optional for private instance)

1. Put new data (samples or annotations) in the immutable storage (e.g. NFS disk share, web folder, or S3 bucket).
2. [Index](Command-summary.md#index) this new data location in LDB.
3. [Stage](Command-summary.md#stage) a dataset in the workspace.
4. [Add](Command-summary.md#add) data to this workspace based on location path, JSON query, file properties, etc.
5. [Commit](Command-summary.md#commit) this dataset so it can be accessed later.
6. [Instantiate](Command-summary.md#instantiate) this dataset to download the data from storage.

6a. Train or validate the model on data, find things to improve in the dataset.

7. Begin new incremental iteration starting from pp. 2, 3, or 4.


# Tutorial


One good example for the data-driven AI task can be derived from the [2021 competition](https://https-deeplearning-ai.github.io/data-centric-comp/) 
by [DeepLearning.AI](http://deeplearning.AI) to train a [ResNet50 model](https://arxiv.org/abs/1512.03385v1) to recognize hand-written roman numerals: 

![roman numerals dataset, courtesy DeepLearning.AI](/images/numerals-deeplearningAI.png)

A [starter set of ~3,000 labeled training images](https://worksheets.codalab.org/rest/bundles/0xcea1d733e1f144d9aba83929af51f191/contents/blob/) is provided in competition, and contestants are free to add more (up to 10,000 images) to score on a leaderboard. The task aims at demonstrating how performance improvements can be achieved with managing data. In this tutorial, we are going to walk through this task using LDB.

To get the optimal performance from an expressive ML model, one needs to solve the following data-specific challenges:

* Cleanse input data. Remove duplicate, irrelevant, or excessively noisy samples.
* Clean input annotations. Make sure annotations match the content of data samples.
* Enrich the data. Find ways to obtain more samples from real world.
* Introduce augmentations to teach the network about data variations and imperfections.
* Add synthetic data (derived from the teacher-student, generative networks, etc.) to cover any remaining gaps.
* Do performance analysis to understand what data causes difficulties or drift and add more samples of this type.

At the level of organization, all these tasks can be reduced to manipulating data collections – such as the original dataset, auxiliary samples, synthesized samples, augmented samples, and so on. If you have not installed LDB yet, let us install it now:

```
pip install 'ldb-alpha [s3,clip-plugin,resnet-plugin]' 
```

We begin with organizing the starter data for the DeepLearningAI challenge into LDB dataset. The starter data is provided in Tensorflow-inferred format (labels derived from folder names), and there is some initial split into test and validation sets that we can mark by setting tags:

```
mkdir Datacentric-competition ; cd Datacentric-competition
ldb stage ds:roman-numerals --target roman-numerals/
ldb index --format infer s3://ldb-public/remote/data-lakes/roman-numerals/val/ --add-tags val
ldb index --format infer s3://ldb-public/remote/data-lakes/roman-numerals/train/ --add-tags train
cd roman-numerals/
ldb add s3://ldb-public/remote/data-lakes/roman-numerals/
ldb commit
```
<details>
  <summary>Output</summary>
	
```
Initialized LDB instance at '/Users/dkh/.ldb/private_instance'
Added storage location '/Users/dkh/.ldb/read_add_storage'
Added storage location 'ldb-public/remote'
Staged new dataset ds:roman-numerals at 'roman-numerals'
	
Data format: tensorflow-inferred

Indexing paths...

Finished indexing:
  Found data objects:       813
  Found annotations:        813
  New data objects:         813
  New annotations:          813
	
Data format: tensorflow-inferred

Indexing paths...

Finished indexing:
  Found data objects:      2067
  Found annotations:       2067
  New data objects:        2018
  New annotations:         2018


Adding to working dataset...
Added 2831 data objects to ds:roman-numerals
	
Committed ds:roman-numerals.v1
```
</details>

## First look at the data

If you examine the indexing output carefully, you can already spot one problem with the starter set: test and validation splits do not add together to the total number of new objects. LDB indexes objects by content (hash), so if the same object was provided in training and validation split, it should have both `train` and `val` tags in our workspace. We can check for existence of such objects with LIST command:

```
ldb list --tag train --tag val
```
<details>
  <summary>Output</summary>

```
Data Object Hash                      Annot  Data Object Path          Transforms              
 id:02d4f6af6de0e622bd67637d1d3620a7   1      ...b317-38f9d35ea60f.png  self
 id:02eb050cd69598c3b0d6cc93611c92a2   1      ...b317-38f9d35ea60f.png  self
 id:0635bd89465729cf84f8598229b0665b   1      ...b317-38f9d35ea60f.png  self
 id:083439bdb2c0591e102addc01b1eb4b3   1      ...b317-38f9d35ea60f.png  self
 id:15bf110e1ca8a4684dfcf3178456b633   1      ...b317-38f9d35ea60f.png  self
 id:1ff7ced1800484161f34715c2172f535   1      ...b317-38f9d35ea60f.png  self
 id:2124746c8162c112926050f7a33c5879   1      ...b317-38f9d35ea60f.png  self
 id:2382f776473ee00daa94676b70ccae75   1      ...b317-38f9d35ea60f.png  self
 id:26297aa20c509bdd08d67a487f6db5a8   1      ...b317-38f9d35ea60f.png  self
 id:2aa3ae4cb092973ccbb288cb3ca03249   1      ...b317-38f9d35ea60f.png  self
 id:2b7bbc6d97cd20fe224b084920c48de0   1      ...b317-38f9d35ea60f.png  self
 id:2d8ce75c8587e262873ffbbe960a941f   1      ...b317-38f9d35ea60f.png  self
 id:2f4d516b268fd579ddfabbcf36068339   1      ...b317-38f9d35ea60f.png  self
 id:37516543f0866bf9253d49589fbd821a   1      ...b317-38f9d35ea60f.png  self
 id:3cfb5d8293557021aa8d32af9aa7c1ee   1      ...b317-38f9d35ea60f.png  self
 id:43235118e60d871949fc5a0ac571f1fd   1      ...b317-38f9d35ea60f.png  self
 id:57c6eac9bb0e7cfd2009c3dce2d98d70   1      ...b317-38f9d35ea60f.png  self
 id:5b3750bf92f0b85c1ec8a5f3a0f380ff   1      ...b317-38f9d35ea60f.png  self
 id:5d83c044920ef7808ddd1cb17ef6899c   1      ...b317-38f9d35ea60f.png  self
 id:5e3bf11e9b39ee7dbaa11aafb519bcc7   1      ...b317-38f9d35ea60f.png  self
 id:66b5767dd4ca79063026defab5719d1e   1      ...b317-38f9d35ea60f.png  self
 id:69c9c2e15e38d32074b5d1c21323bde2   1      ...b317-38f9d35ea60f.png  self
 id:6be2772a1688a897f0710addee0221c5   1      ...b317-38f9d35ea60f.png  self
 id:726ccf326a1cb4ba0e8e614a5d393449   1      ...b317-38f9d35ea60f.png  self
 id:727d95b1ecc3b80f1e17cb40e1495cc3   1      ...b317-38f9d35ea60f.png  self
 id:73d682eabd8fc2f6107bc85c2392ddf7   1      ...b317-38f9d35ea60f.png  self
 id:7bce7e64fabf477c8e6380030c30f1ea   1      ...b317-38f9d35ea60f.png  self
 id:7d1cc809c0ab2ae3fe1ce90517a34d9c   1      ...b317-38f9d35ea60f.png  self
 id:80204a23356d089b1c3a4edea5bebc0a   1      ...b317-38f9d35ea60f.png  self
 id:82a7c1753b187d235f521c6dd92a59d8   1      ...b317-38f9d35ea60f.png  self
 id:8b2d92d718ee30b372af735ecefd9d7a   1      ...b317-38f9d35ea60f.png  self
 id:9334c45729f357c7cd3bad4120455831   1      ...b317-38f9d35ea60f.png  self
 id:a01aeaed7c19d9859072553d73743288   1      ...b317-38f9d35ea60f.png  self
 id:a08a04977bbe82411752ed4b6e6fd506   1      ...b317-38f9d35ea60f.png  self
 id:a5c566a35567bee4b3d6db89b497cb8b   1      ...b317-38f9d35ea60f.png  self
 id:a5d5f8695908c027e9308be9cb783ceb   1      ...b317-38f9d35ea60f.png  self
 id:a69d9477813a8ebe3a49635a3b6c43ef   1      ...b317-38f9d35ea60f.png  self
 id:a7ff90ac601e6fdfeb5b38a553a4d458   1      ...b317-38f9d35ea60f.png  self
 id:aec7d3aaf85e4f6753f37681a202156e   1      ...b317-38f9d35ea60f.png  self
 id:b3e72f4413d1dfa9eef47a0717f4ca90   1      ...b317-38f9d35ea60f.png  self
 id:c9a89776993c2f39896c091548f91708   1      ...b317-38f9d35ea60f.png  self
 id:ce8f893cabf9865166f1d8493be9a6f5   1      ...b317-38f9d35ea60f.png  self
 id:d1c1f943855515001c6fab7e7b07b7ba   1      ...b317-38f9d35ea60f.png  self
 id:da599da573ce096f012a95534caab5fd   1      ...b317-38f9d35ea60f.png  self
 id:ddd1931485d742e46866350ff16b5fc5   1      ...b317-38f9d35ea60f.png  self
 id:eaf7fdda144f71f3770d451972a3e377   1      ...b317-38f9d35ea60f.png  self
 id:ee465a602e63d7c5dd4b3d1f7f9530dd   1      ...b317-38f9d35ea60f.png  self
 id:ee86c80c7fd5e020f0c52bf5f621dba7   1      ...b317-38f9d35ea60f.png  self
 id:f1f7f68daa670efb578839b8fd0dd713   1      ...b317-38f9d35ea60f.png  self	
```
</details>
	
Next let's do another sanity check and see the balance of classes in splits. For that, we can peek at the JSON layout for the first duplicate object:

```
ldb eval id:02d4f6af6de0e622bd67637d1d3620a7
```
<details>
  <summary>Output</summary>

```
id:02d4f6af6de0e622bd67637d1d3620a7
{
  "label": "i"
}
```
</details>
As we see from the annotation, Tensorflow-inferred format was translated in LDB into JSON schema with key `label` describing the object class. We can use this key to tally classes with a JMESPATH query:

```
ldb eval -j --tag val --query 'label'  | sort | uniq -c
ldb eval -j --tag train --query 'label'  | sort | uniq -c
```

<details>
  <summary>Output</summary>

```
  82 "i"
  81 "ii"
  79 "iii"
  84 "iv"
  81 "ix"
  83 "v"
  82 "vi"
  77 "vii"
  83 "viii"
  81 "x"
	
 261 "i"
 157 "ii"
 186 "iii"
 281 "iv"
 234 "ix"
 196 "v"
 181 "vi"
 193 "vii"
 199 "viii"
 179 "x"
	
```
</details>
	
There is clearly imbalance in training set, especially for `ii` and `iv` labeled objects. 
		

## Model evaluation harness

Ability to train the model, evaluate it and quickly return to editing the dataset is key to Datacetric AI. Let us organize our workflow around this idea. 

We left the previous section in the folder named "./roman-numerals" which was staged as namesake LDB dataset. This will be our workspace for iterating on numeral images. For training the ResNet50 model, we will need to split the numerals dataset into training and validation. We will also need a folder to store model predictions, so let us create those:

```
cd .. ; mkdir train; mkdir val; mkdir predictions
```

Besides, we will need the ResNet model itself, and a test dataset (labelbook) to evaluate the final score after training. In the Datacentric-AI competition, a testset that drives the leaderboard was hidden, so hand-picking convincing labelbook samples remained a responsibility of the participants.  

In this tutorial we will use [labelbook by Kenneth Leung](https://github.com/kennethleungty/Data-Centric-AI-Competition) and ResNet code modified for our folder layout:

```
curl -L https://remote.ldb.ai/datasets/ResNet50/ResNet50.tar.gz | tar xz
```

At this point, our project top directory should look like this:

```
Datacentric-competition
	.
	├── inference.py
	├── train.py
	├── roman-numerals/
	├── train/
	├── val/
	└── predictions/
```

The last thing we need to do before training the model on stock dataset is to instantiate our default splits:

```
cd roman-numerals/
ldb instantiate --tag train --target ../train
ldb instantiate --tag val --target ../val
```

This should be all we need to train our baseline model (if you don't have Tensorflow and Keras, look for help [here](https://www.tensorflow.org/install)).

```
python train.py
```
<details>
  <summary>Output</summary>
  output
</details>



----------TODO---------


For now let us delete tag `train` from all duplicates:

```
ldb tag --tag val --tag train --remove train
```
<details>
  <summary>Output</summary>
	
```
Tagging data objects
  Data objects:       49
  Num updated:        49
```
</details>
	
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
| Add visually similar images to a working dataset  | `$ ldb add gs://iterative/handwritten --pipe clip-text "iii" --limit 100` |


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


