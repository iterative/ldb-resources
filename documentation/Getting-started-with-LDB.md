# LDB getting started

LDB is an MLOps tool that indexes the existing immutable storage for data files and allows for easy construction of datasets based on metadata queries. 
This datasets are meant to be used for training models, and further updated based on the model performance (Data-driven AI).

A good example for the data-driven AI can be derived from the [2021 competition](https://https-deeplearning-ai.github.io/data-centric-comp/) 
from [DeepLearning.AI](http://deeplearning.AI) to train a ResNet-50 model to recognize hand-written roman numerals. 
A starter set of ~3,000 labeled images is provided, and contestants are free to compile a training set of up to 10,000 images that will perform 
the best on the test set:

![roman numerals dataset, courtesy DeepLearning.AI](/images/numerals-deeplearningAI.png)


Let us assume we embark on a similar path of iterating on data. 
To get the optimal performance from a deep learning network, one generally needs to solve the following data problems:

* Cleanse the data objects. Remove duplicates, irrelevant, or excessively noisy samples.
* Clean annotations. Make sure annotations match the content of data samples.
* Enrich the initial sample set. Find creative ways to obtain more data from the real world.
* Introduce effective transformations to teach the network to deal with variations.
* Add effective synthetic samples (teacher-student samples, GAN samples, etc.)

At the level of data organization, all these tasks can be reduced to manipulating the membership information on multiple related 
(and possibly overlapping) collections - such as original data samples, auxiliary samples, synthesized samples, transformed samples, and so on.

LDB makes the dataset manipulation and version tracking simpler by indexing unique data objects, 
constructing the datasets by querying their metadata and content, and versioning the results.

To demonstrate a sample workflow in LDB, let us start from creating the dataset that will hold all original input data. 
Assuming it lives in ~/roman/input let us STAGE a matching dataset named *"numerals"* in the workspace and ADD all data objects (with annotations) 
from this directory:

| Step | Command |
| --- | --- |
| Start a new dataset in the workspace | `$ ldb stage ds:numerals` |
| Add objects from a given path | `$ ldb add ~/roman/input` |



Now we have created a dataset named *"numerals"* in our workspace. Since LDB datasets are logical entities, no data objects were copied or moved. 
Instead, LDB have parsed the provided location, found all unique data samples (ignoring any duplicates), parsed their annotations and stored 
these pointers in the workspace. To save this dataset for further inquiries, let us push it back into LDB repository:

| Step | Command |
| --- | --- |
| Save dataset "numerals" into LDB, v.1 | `$ ldb commit` |


Now let us assume we have trained a ResNet-50 network on the provided original dataset, and for each training sample acquired the output inferences 
in annotation format where "truth" is the input object class (label), and "inference" is the network's output:

```json
{
		   "path": "./i/125d.jpg"
			 "class": "i",
		   "inference": {
				 "class": "ii",
				 "confidence": 0.2,
			 }
}
```

For the sake of example, let us assume that output annotations were stored alongside the original data samples in a directory `~/roman/output` (yes, we know this duplicates data objects, but just bear with us for now).

As usual for inferences, from the output annotations we can observe that some training examples were not generalized properly, 
or their output inference probability was low. This could signal a few things: first, the underlying image could be incorrect or noisy, 
or the provided label is wrong.

Therefore, let us isolate these objects into a separate dataset `"numerals-to-examine"`.  
We can create it by staging a new dataset and querying annotations to ADD objects:


| Step | Command |
| --- | --- |
| Start a new dataset  | `$ ldb stage ds:to-examine` |
| Add objects missing classification | `$ ldb add ~/roman/output --query class != inference.class` |
| Add objects with low confidence | `$ ldb add ~/roman/output --query inference.confidence < 0.75` |


Now we created a dataset `"to-examine"` that holds references to objects we want to check manually. 
However, there are no files to look upon in our workspace yet. This is because LDB datasets are logical entities. 
To instantiate this dataset (transfer the relevant objects from storage location), use the INSTANTIATE command:

| Step | Command |
| --- | --- |
| Instantiate "to-examine" dataset in a workspace  | `$ ldb instantiate` |


At this point, let us assume we have got ten annotated images, which look somewhat like this: 

![Courtesy: DeepLearning.ai, subset of images compiled by Pierre-Louis Bescond.](/images/numerals-bescond.png)



Here, the second image in the top row is too noisy to recognize even for a human, and the third image on the bottom row clearly does not belong to a set. The very first image should have been easy to recognize, but carries the wrong annotation, while the others present challenge types the network is not dealing gracefully with.  For now, let us assume we want delete all these images from the training set going forward. 

To accomplish this task, we can save the dataset "to-examine", stage our main working dataset, and subtract the former from the latter:


| Step | Command |
| --- | --- |
| Save "to-examine" dataset   | `$ ldb commit` |
| Stage "numerals" dataset | `$ ldb stage ds:numerals` |
| Subtract contents of a dataset| `$ ldb delete ds:to-examine` |
| Save dataset "numerals" v.2 | `$ ldb commit` |

Now we have modified our working dataset and can instantiate it in workspace and re-train the model if needed. But let us pretend we do not like the result and want to roll back the changes. LDB versions datasets and annotations for each object to make it easy.  All we need to get back to the previous version is to stage it and push as a new dataset revision:


| Step | Command |
| --- | --- |
| Stage a specific dataset version  | `$ ldb stage ds:numerals.v1` |
| Save it as the "current" version | `$ ldb commit` |


At this point, LDB holds two revisions of dataset "numerals", v.1 and v.2, and the former is the current version that will be checked out by default.

### More dataset manipulations

In a given example, we saw how a dataset can be staged, instantiated, filled, and modified.

If you plan to work further on the roman numerals challenge, you will likely need more operations. For example, to add more roman numerals from other data sources, you need to find these datasets and bring them into LDB. Then you need to query them for the desired image classes and sample into your main working dataset to preserve class balance.

Similarly, at some point you may choose to add more images visually similar to the styles that underperform in your model. In that case, you may find queries using the helper ML models to come handy.  

You can read more on [LDB Query Language here](LDB-Query.md).

### LDB index and storage re-indexing

So far in our example, we have assumed that LDB parses annotations during ADD command that is given location of data, and uses those key-value pairs as a basis for query filters.

As your data storage grows, this assumption will no longer hold true. For instance, you could have accumulated roman numeral images from multiple sources, and no longer remember their relative paths in storage. Or you have a storage that is shared among several projects. Or you are using cloud storage, where buckets do not correspond to search terms. 

You should be relieved to know that LDB adds every new annotation into internal database (index), that will be queried by default when no explicit path or a dataset is provided as a basis for query. 

However, this still leaves two questions in place: first, what if you want to update annotations for existing data samples? And second, if annotations are updated in LDB, what happens to datasets using old annotations?

To answer the first question, LDB support the re-indexing operation, where any storage location can be asynchronously queried for new data objects and annotations. New (previously unseen) pieces of information are added to LDB. To answer the second question, LDB keeps track of annotation versions. This means if some dataset uses a data object with annotation v.1 and later this annotation is updated to v.2, this same dataset will always check out with annotation v.1 to ensure  result reproducibility. However, any new reference to this data object will default to the updated version (v.2), so changes can be picked up if needed.
