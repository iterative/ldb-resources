Alternatives to virtual dataset storage in LDB.

1. Folder-level dataset organization.

The default method to create datasets is by copying data samples into named file folders. This method has an advantage of being the simplest way to bootstrap a new project, yet it comes with serious limitations:

* Experimenting on data (adding or removing data objects) results in multiple copies of the *same* dataset with minimal changes – which is undesirable for datasets of non-trivial sizes.

* Folders are not easy to slice and dice, and retain no metadata to keep track of changes and object provenance (which data sample came from which source). 

* Attempts to add new data objects may result in repetitions (same object under multiple names), or data loss (samples overwritten by mistake).

* Annotation updates are not tracked, which may cause annotations going stale.

* Unrestricted folder-level modifications are difficult to integrate with privacy policies and access directives.

2. Spreadsheets, or other database-powered datasets design.

A reasonable step up from managing datasets in folders is to organize them as spreadsheets filled with object pointers (URIs of data objects living in cloud locations). 

This method permits for sparse datasets where individual objects are no longer required to reside in one folder or cloud bucket. Since spreadsheet-based datasets decouple storage from membership, they no longer require objects to be copied or moved to form new datasets, permit to store provenance meta-information as attributes, and can be compatible with privacy policies. In addition, versioning for datasets and annotations can be provided for by means of storing multiple linked tables corresponding to versions.

Spreadsheets, however, still carry significant limitations: 

* They do not solve the problem of repetitions (same data objects listed under different URIs), and cannot prevent annotations from going stale. Both of these problems require tracking objects by content which spreadsheets cannot do.

* Spreadsheets do not provide native means to assemble datasets with queries. This means an ML engineer needs to compose them manually, or use ad-hoc software to query annotations and export lists of the matching objects into the spreadsheets and tables.

* Use of spreadsheets and databases to store datasets forces ML engineers to use unfamiliar tools that are hard to integrate with MLOps. Forming a dataset and registering it in a database is a prcess with many touching points.

3. Heavyweight ML frameworks.

It is fairly common to find parts of functionality offered by LDB in the large, heavyweight ML frameworks. For example, any data labeling software suite likely has some function to track annotation versions and search annotations by fields. Likewise, every end-to-end ML platform facilitates organization of input data into the datasets, at least at the folder level. 

While heavyweight ML platforms can be very successful in vertical-specific applications, they are difficult to recommend as one-size-fits-all tools.

Unlike these platforms, LDB follows Unix toolchain philosophy and solves exactly one problem – it sits between the (immutable) data storage and mutable model training workspace, and allows for reproducible and fast data-driven ML iteration. This enables an easy integration with any labeling software upstream, or any experiment automation downstream.
