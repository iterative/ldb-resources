# LDB team setup #

When starting a shared LDB instance, the first decision is where to house it. 

A shared LDB instance must reside in a shared filestystem folder that is available for all team members, and fast enough for queries to operate efficiently. In the below example, a drive mounted at location `/data` is shared across the ML team, and LDB instance is placed into folder `corporate-LDB` 

### Setting up a new LDB instance

| Step | Command |
| --- | --- |
| Create a new LDB instance | `$  ldb init /data/corporate-LDB` |


When running LDB commands, they need to be pointed towards an active LDB instance. This is done with one of the two methods: an environment variable or a configuration file. By default, an LDB configuration file is expected to reside in the user home directory, folder '.ldb' but if both pointer types are present, an environment variable will take precedence:

| Step | Command |
| --- | --- |
| Save LDB location into environment | `$  export LDB_DIR=/data/corporate-LDB` |
| Save LDB location into a configuration file | `$ mkdir ~/.ldb; echo "LDB_DIR=/data/corporate-LDB" > ~/.ldb/.config` |

### Registering new LDB storage locations

LDB assumes data objects are immutable and live in the pre-defined storage locations (cloud buckets or datalake folders). 

A good engineering discipline is to gate access to these locations to ensure the data objects are not accidentally moved or deleted. LDB supports local storage, AWS, Google Cloud, and Azure as storage targets. LDB configuration to access these cloud providers is discussed in [Setting Access to Cloud Locations](/TODO).

You can add new storage locations to LDB at any time, but you cannot remove storage locations that are already referenced in the existing datasets.

| Step | Command |
| --- | --- |
| Add a new storage location | ` $  ldb add-storage gs://my-awesome-bucket/` |

### Registering a "read-add" storage location

By default, LDB only allows for objects from immutable storage locations. LDB only needs read and stat permissions for those locations and relies on external data engineering processes to get new samples there. However, in some cases, it is convenient to add new samples to LDB index right when you work in your data workspace. For example, an engineer may choose to quickly modify an image, auido record, or text while browsing data in LDB workspace.

In that case, LDB can be configured to support a 'read-add' storage location where new data objects are copied when indexing from emphemeral locations (such as  a workspace). This configuration must be explicitily specified, and will require "append" privileges at this location:

| Step | Command |
| --- | --- |
| Add a new 'read-add' storage location | ` $  ldb add-storage -a gs://our-append-bucket/` |


