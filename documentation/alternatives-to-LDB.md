## Alternatives in dataset organization: ##

Here we discuss some popular dataset organization methods.

### Folder-level dataset organization. ###

The simplest method to manage datasets is by grouping samples into named file folders. Many popular datasets (COCO, ImageNet, etc) are shipped as folders, and most Kaggle datasets will look as folders after setting them up.

This method is great when work focuses on the AI models, yet it leads into serious limitations with Data-Centric AI:

* Experimenting on dataset (adding or removing data objects) results in multiple copies of the *same* dataset with minimal changes.

* Folders are not easy to slice and dice, and retain no metadata to keep track of changes and object provenance (which sample came from where). 

* Attempts to add new samples may produce repetitions (same objects under multiple names), or data loss (samples overwritten by name collisions).

* Annotation updates are not versioned, which may cause annotations going stale.

* Folder-level access granularity is difficult to integrate with privacy policies and data access directives.

### Spreadsheets (or other database-powered designs). ###

A reasonable step up from managing datasets in folders is to organize them as tables filled with pointers (URIs of data objects). 

This method permits for sparse datasets where individual objects are no longer required to reside in one folder or cloud bucket. Since spreadsheet-based datasets decouple storage from membership, they no longer require objects to be copied (or moved) to form new datasets, and allow to store any meta-information as attributes. In addition, versioning for datasets and annotations can be provided by means of multiple tables corresponding to different versions.

Spreadsheets, however, still carry significant limitations: 

* They do not solve the problem of repetitions (same data objects listed under different URIs), and cannot prevent annotations from going stale. Both of these problems require tracking objects by content which spreadsheets cannot do.

* Spreadsheets do not provide native means to assemble datasets from queries. This means an ML engineer needs to compose object lists manually, or use ad-hoc software to query annotations and export matching objects into the tables.

* Use of spreadsheets and databases to store datasets forces ML engineers to use unfamiliar tools that are hard to integrate with MLOps. Forming a dataset and registering it in a database is a process with many touchpoints.

### Heavyweight ML frameworks ###

Finally, it is fairly common to find dataset management functions in the large, heavyweight ML frameworks. For example, any data labeling software likely has some ability to track annotation versions and search annotations by fields. Likewise, every end-to-end ML platform facilitates some organization of input data into the datasets, at least at a folder level. 

While heavyweight ML platforms can be extremely successful in vertical-specific applications, they are difficult to recommend for everyone.

Unlike these platforms, LDB follows Unix toolchain philosophy and solves exactly one problem – it sits between the (immutable) data storage and mutable model training workspace, and allows for reproducible and fast data-driven ML iteration. This enables an easy integration with any labeling software upstream, or any experiment automation downstream.
