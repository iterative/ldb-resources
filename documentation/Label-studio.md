# LDB and Label Studio

## Roman Numeral Bounding Boxes

This example shows how to use LDB alongside Label Studio. The basic steps are:

1. Use LDB to download some data from a remote data lake.
2. Use Label Studio to annotate this data.
3. Import your Label Studio annotations back into LDB.

This assumes you have both `ldb` and `label-studio` installed. Separate virtual envs for each is recommended:
```bash
pip install ldb-alpha
pip install label-studio
```

Create a new ldb instance, and index some data:
```bash
mkdir -p ~/projects/roman-numerals
cd ~/projects/roman-numerals

export LDB_DIR="$PWD/instance"
ldb init "$LDB_DIR"
ldb add-storage s3://ldb-public/remote -o anon true
ldb index --format infer s3://ldb-public/remote/data-lakes/roman-numerals/val/
ldb instantiate ds:root --limit 3 -t data
```

In another terminal, navigate to this same directory and use label studio's script to host these files locally:
```bash
cd ~/projects/roman-numerals
wget https://raw.githubusercontent.com/heartexlabs/label-studio/3b394c3bf997abe28100e4ef4143f347f6083a69/scripts/serve_local_files.sh
./serve_local_files.sh data '*.png'
```

This will create a `files.txt` file in the current directory with a list of localhost URL's. 

Leave this process running while you import data to Label Studio, annotate it, export the annotations, and index the new annotations with LDB. If you stop it at any point, simple run the last command again to start it.

Now you can start a Label Studio instance:
```bash
label-studio start --username user@example.com --password your-password --user-token abc123
```

This should open a browser window with a Label Studio UI. You can login with the username and password from the previous command. Now you may do the following steps from the UI or command line:
1. Create a new project
2. Import `file.txt`. In the UI, if prompted with an option "Treat CSV/TSV as [ ] List of tasks [ ] Time Series", select "List of tasks".
3. Add your labeling configuration. In the UI, navigate within your project to Settings > Labeling Interface and paste the config into the Code box. Then click save.

To create a new project and import the `files.txt` file from the command line, replace `abc123` with your token and run:
```
curl -H Content-Type:application/json -H 'Authorization: Token abc123' -X POST 'http://localhost:8080/api/projects' --data "$(cat config.xml | jq -R --slurp '{label_config: .}')"
curl -H 'Authorization: Token abc123' -X POST 'http://localhost:8080/api/projects/1/import' -F file=@"$HOME/projects/roman-numerals/files.txt"
```

Now you can annotate your files in the Label Studio UI, by clicking on tasks, selecting the label and marking a bounding box. For example you may want to create new samples by taking an image of `IX` and marking the `I` and the `X` separately.

Finally, export your newly annotated data in the JSON format using the "Export" button in the UI, or by running:
```bash
curl -X GET http://localhost:8080/api/projects/1/export?exportType=JSON -H 'Authorization: Token abc123' --output 'annotations.json'
```

Now you may index this file to import these annotations into LDB:
```bash
ldb index --ephemeral-remote --format label-studio annotations.json
```

Now to see the bounding boxes of updated annotations, run:
```bash
ldb eval ds:root --query annotations --query 'annotations[].result[].value' 
```
