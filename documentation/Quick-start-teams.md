When starting a shared LDB instance, the first decision is where to house it. LDB instance must reside on a disk location reachable for all team members, and fast enough for queries to operate efficiently. In the below example, a drive mounted at location `/data` is shared between the ML engineers, and LDB instance is created in folder `corporate-LDB` 

### Setting up a new LDB instance

| Step | Command |
| --- | --- |
| Create a new LDB instance | `$  ldb init /data/corporate-LDB` |

LDB command-line tools can be pointed to an active instance with two methods: environment or a configuration file. If both methods are present, environment variable will take precedence:

| Step | Command |
| --- | --- |
| Save LDB location into environment | `$  export LDB_ROOT=/data/corporate-LDB` |
| Save LDB location into configuration file | `$ mkdir ~/.ldb; echo "LDB_ROOT=/data/corporate-LDB" > ~/.ldb/.config` |

### Registering new LDB storage locations


LDB assumes data objects are immutable and live in the pre-defined storage locations (cloud buckets or datalake folders). A good engineering discipline is to gate access to these locations to ensure the data objects are not accidentally moved or deleted. LDB supports local storage, AWS, Google Cloud, and Azure as storage targets. LDB configuration to access these cloud providers is discussed in [Setting Access to Cloud Locations](/TODO).

You can add new storage locations to LDB at any time, but you cannot remove storage locations that are already referenced in the existing datasets.

| Step | Command |
| --- | --- |
| Add a storage location | ` $  ldb add-storage gs://my-awesome-bucket/` |
| Verify current LDB storage locations | `$  ldb status ds:root` |


### Indexing and re-indexing storage

Once LDB instance is set, it will maintain index of data objects and annotations. This index needs to be updated whenever new objects or annotations become available. Note, that LDB indexes only unique data objects (ignoring duplicates), and registers new label versions only if it encounters annotation updates.

| Step | Command |
| --- | --- |
| Index new objects in a storage folder | `$  ldb index gs://my-awesome-bucket/new-data/` |
| Verify that new objects appear in index | `$  ldb list ds:root` |

