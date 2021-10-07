### Setting new LDB instance

LDB assumes data objects are immutable and live in the pre-defined storage locations (cloud buckets or folders). You can add new storage locations to LDB at any time, but you cannot remove storage locations that are already referenced in the existing datasets.

| Step | Command |
| --- | --- |
| Create a new LDB instance | `$  ldb init /data/myLDB` |
| Save LDB location into environment | `$  export LDB_ROOT=/data/myLDB` |

### Registering LDB storage locations

| Step | Command |
| --- | --- |
| Add a storage location | ` $  ldb add-storage gs://my-awesome-bucket/` |
| Verify current LDB storage locations | `$  ldb status ds:root` |

Once LDB is up and running, it can rebuild the index whenever new objects or annotations become available. Note, that LDB indexes only unique data objects (ignoring duplicates), and registers new label versions only if it encounters annotation updates.

### Indexing and re-indexing storage

| Step | Command |
| --- | --- |
| Index new objects in a storage folder | `$  ldb index gs://my-awesome-bucket/new-data/` |
| Verify that new objects appear in index | `$  ldb list ds:root` |
