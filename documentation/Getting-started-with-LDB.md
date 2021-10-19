# LDB workflow

LDB is an MLOps tool that indexes the existing immutable storage for data files and allows for easy construction of datasets based on metadata queries. 
These datasets are meant to be used for model training, and are usually further updated based on the model performance (Data-driven AI loop).

A good example for the data-driven AI task can be derived from the [2021 competition](https://https-deeplearning-ai.github.io/data-centric-comp/) 
by [DeepLearning.AI](http://deeplearning.AI) to train a ResNet50 model to recognize hand-written roman numerals. 

![roman numerals dataset, courtesy DeepLearning.AI](/images/numerals-deeplearningAI.png)

A starter set of ~3,000 labeled images is provided, and contestants are free to compile a training set of up to 10,000 images to perform best on a test set.
To get the optimal performance on a sufficiently expressive deep learning network, one generally needs to solve the following data problems:

* Cleanse data objects. Remove duplicates, irrelevant, or excessively noisy samples.
* Clean annotations. Make sure annotations match the content of data samples.
* Enrich the initial sample set. Find creative ways to obtain more data from the real world.
* Introduce effective augmentations to teach the network to deal with variations.
* Add effective synthetic samples (teacher-student, GAN, etc.) to cover any remaining data gaps.

At the level of data organization, all these tasks can be reduced to manipulating the membership information in
(possibly overlapping) data collections – such as original data samples, auxiliary samples, synthesized samples, transformed samples, and so on.

LDB makes the dataset manipulation and version tracking simpler by indexing unique data objects, 
constructing the datasets by querying their metadata and content, and versioning the results.

To demonstrate a sample workflow in LDB, let us begin with creating a dataset that holds the original (input) data for the DeepLearningAO challenge. 
Assuming the data was downloaded to `/storage/input` let us create a dataset called `"numerals"` in the workspace to hold input data:

| Step | Command |
| --- | --- |
| Start a new dataset in the workspace | `$ ldb stage ds:numerals` |
| Add objects from a given path | `$ ldb add /storage/input` |


Now we have created a new dataset named `"numerals"` in our workspace and filled it with input references. LDB datasets are logical entities, so no data objects were copied or moved. Instead, LDB have parsed the provided location, found all unique data samples (ignoring any duplicates), parsed their annotations and stored 
these pointers in the workspace. It is important that data in `/storage/` remains accessible for LDB because LDB relies on storage immutability.

To save this dataset for further steps in the workflow, let us store it into LDB repository:

| Step | Command |
| --- | --- |
| Save dataset "numerals" into LDB, v.1 | `$ ldb commit` |


The DeepLearningAI competition comes with a ResNet50 docker images to evaluate the dataset. In order to simulate the competition backend, let us assume the network was trained on the provided (original) data, and for every training sample the network produced inferences in JSON format, where "class" is the input label, and "inference" is the output label:

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

For the sake of example, let us assume these output annotations were stored alongside the original data samples in a directory `/storage/output`.

As usual for inferences, from these output samples we can observe that some training inputs were not generalized properly, 
or their prediction confidence remained low. This could tell us a few things: first, the underlying data object could be noisy or incorrect, 
or it could be paired with a wrong label.

To investigate further, let us isolate these objects into a separate dataset.  
We can create it by staging a new dataset and querying annotations from network output to add objects into it:


| Step | Command |
| --- | --- |
| Start a new dataset  | `$ ldb stage ds:to-examine` |
| Add objects missing classification | `$ ldb add /storage/output --query class != inference.class` |
| Add objects with low confidence | `$ ldb add /storage/output --query inference.confidence < 0.75` |


Now we have created a dataset `"to-examine"` that holds references to data objects that we want to inspect manually. 
However, there are no files to examine in our workspace yet. This is because LDB datasets are logical entities. 
To instantiate this dataset (transfer the relevant objects from storage location), we will use the INSTANTIATE command:

| Step | Command |
| --- | --- |
| Instantiate "to-examine" dataset in a current workspace  | `$ ldb instantiate` |

At this point, let us assume the dataset "to-examine" holds ten annotated images, which look somewhat like this: 

![Courtesy: DeepLearning.ai, subset of images compiled by Pierre-Louis Bescond.](/images/numerals-bescond.png)


Here, we observe that a second image in the top row is too noisy to recognize (even for a human), and the third image on the bottom row does not belong to a set. On the other hand, the very first image should have been easy to recognize, but possibly carries the wrong annotation, while the others perhaps present some challenges the network is not dealing gracefully with. For now, let us try to delete these images from the training set and see if the network does better.

To accomplish this task, we can save dataset `"to-examine"`, stage our main working dataset, and subtract the former from the latter:


| Step | Command |
| --- | --- |
| Save "to-examine" dataset   | `$ ldb commit` |
| Stage "numerals" dataset | `$ ldb stage ds:numerals` |
| Subtract contents of a dataset| `$ ldb delete ds:to-examine` |
| Save dataset "numerals" v.2 | `$ ldb commit` |

Once we have successfully modified our working dataset, and can instantiate it the workspace to re-train the model (if needed). But let us pretend we have changed our mind and want to roll back the changes. LDB versions the datasets and annotations for each object to make it easy. All we need to get back to the previous dataset version is to stage it and push as a new revision:

| Step | Command |
| --- | --- |
| Stage a specific dataset version  | `$ ldb stage ds:numerals.v1` |
| Save it as the "current" version | `$ ldb commit` |

At this point, LDB holds two revisions of the dataset "numerals", v.1 and v.2, and the former is the current version that will be checked out by default.

### More dataset manipulations

In a given example, we saw how a dataset can be staged, instantiated, filled, evaluated and modified, thus closing the data iteration loop.

If you plan to work further on the roman numerals challenge, you will require need more operations. 
For instance, let us assume you need more samples of numeral "i". The easiest way to do that is to find some third-party datasets for this task and store them on your system. Then you need to query them for the desired image class and sample the right number of relevant images preserving the class balance. This task could be accomplished withlike this:

| Step | Command |
| --- | --- |
| Create a new dataset  | `$ ldb stage ds:alternative-numerals` |
| Fill it from alternative storage location | `$ ldb add gs://handwritten-numerals` |
| Check the number of data samples in the interesting class | `$ ldb list --query class == "i" ` |
| Save dataset "alternative-numerals" and stage "numerals" back | `$ ldb commit; ldb stage ds:numerals` | 
| Fill "numerals" with desired class samples |   `ldb add ds:alternative-numerals --limit 100` |


Similarly, at some point you may choose to add more images visually similar to the styles that underperform in your model. In that case, you may find queries using the helper ML models to come handy. You can read more on [LDB Query Language here](LDB-queries.md).

### LDB index and storage re-indexing

So far in our example, we have assumed that LDB parses annotations on the fly when a given location is queried by ADD or a LIST command. 

As your data storage grows, this assumption would be suboptimal. Repeated queries would be very slow, and tracking content by storage location is cumbersome. Instead, LDB adds every new data object and annotation it ever comes across into internal database (index). Index has a pseudo-name "root dataset", and can be referenced as `ds:root`. Thus, looking for a specific data object based on the previously indexed annotation field (or tag) can look simply like this:

| Step | Command |
| --- | --- |
| List objects matching annotation field in the index | `$ ldb list ds:root --query class == "i" ` |
| List objects matching a tag in the index  | `$ ldb list ds:root --tag "training" `| 

Note, that LDB addresses data objects by hashsum, and therefore only keeps track of unique data samples. However, data objects are often coupled with annotations that may change over time. This presents two problems: first, how to update an annotation in LDB, and second – how to ensure reproducibility in dataset if annotations are a moving target?

To answer this challenge, LDB support the re-indexing operation and annotation versions. Re-indexing command asynchronously queries specified storage path for new data objects and annotations and adds them to the index. However, when adding a new annotation, LDB also retains a previous version (if any). This ensures that datasets referencsing previous annotation will remain reproducible.

| Step | Command |
| --- | --- |
| Reindex objects at a given location | `$ ldb index /storage/` |
