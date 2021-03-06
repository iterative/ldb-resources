# Query examples

LDB uses [JMESPATH](https://jmespath.org/specification.html) as a query language over JSON annotations. This allows for complicated data selection and statistics that would normally require custom programming.

The way LDB treats JMESPATH expressions is as follows:

- All query-enabled commands expand the provided list of objects and evaluate JMESPATH over annotations one-by-one.
- **ADD**, **DEL**, **LIST** evaluate the result of JMESPATH as true/false – which determines whether an object is selected for processing. Rules for "falsy" evaluation are as follows: `boolean false, null, empty object, empty list, empty string` (i.e. `[]`, `{}`, `""`, `false`, `null`). 
[Everything else, including `0` and `0.0` evaluates to `true`.](https://jmespath.org/specification.html#or-expressions)


`Tip` one common mistake to watch: ``` `null` == `null` ``` -> True

If you evaluate one "falsy" key against another, the result is a match. See "Get objects where certain key is not null or false" below. 

- Use the **EVAL** command to print raw JMESPATH query output over annotations
- LDB uses `--query` flag to scan object annotations, and `--file` flag to scan file attributes formatted as JSON. These flags can be pipelined.

Here are some query examples, from simple to more advanced:

- **Get objects of certain class**
    
    Input: dataset where image objects have annotations with "class" JSON field:
    
    ```json
    {
      "class": "cat",
      "breed": {
        "type": "main-coon",
        "size": "large"
      }
    }
    ```
    
    Goal: select objects of certain class
    
    ```bash
    # note backquotes around  literal
    ldb add ds:root --query 'class == `cat`'
    ```
    
- **Get objects where attribute compares against numeric constant**
    
    Input: dataset where image objects have annotations with "confidence" JSON field:
    
    ```json
    {
      "class": "airpods",
      "inference": {
        "class": "beats",
        "confidence": 0.7
      }
    }
    ```
    
    Goal: select objects with confidence above certain threshold
    
    ```bash
    # note backquotes on literal
    ldb add ds:root --query 'inference.confidence >= `0.8`' 
    
    ```
    
- **Get objects where inference differs from ground truth**
    
    Input: dataset where objects have annotations with ground truth ("class") and "inference" JSON fields:
    
    ```json
    {
      "class": "airpods",
      "inference": {
        "class": "beats"
      }
    }
    ```
    
    Goal: print objects where two keys pass a comparison test
    
    ```bash
    
    ldb add ds:root --query 'inference.class != class'
    ```
    
- **Compare attribute against JSON object literals**
    
    Input: Dataset consisting of random objects.
    
    ```json
    {
      "class": "airpods",
      "inference": {
        "class": "pro",
        "confidence": 0.7
      }
    }
    ```
    
    Goal:  compare a key against a JSON object literal
    
    ```bash
    # note use of backquotes and swapped keys in the object
    ldb list --query 'inference == `{"confidence": 0.7, "class": "pro"}`'
    
    ```
    
- **Dealing with objects where certain key can be missing or null**

  The original JMESPATH specification assumes a missing JSON key to return `null`, which may lead to unintended consequences – e.g. when comparing one missing key to another missing key (this would somewhat unexpectedly return `true`). LDB query implementation therefore differs from JMESPATH standard by means of immediately skipping an object where annotation has referenced missing key. A separate `--jquery` flag exists for full compatibility with JMESPATH standard with respect to missing keys.
    
    Input: dataset where objects have annotations with "class" JSON field:
    
    ```json
    {
      "class": "cat",
      "breed": {
        "type": "main-coon",
        "size": "large"
      }
    }
    ```
    
    Goal: print all objects where `breed.type` key is not missing, empty or null:
    
    ```bash
    # non-"falsy" key is resolved to "true"
    ldb list --query breed.type
    ```

    Goal: print all objects where `breed.type` is not missing (but can be empty or null):
    
    ```bash
    # this query fails only if the key does not exist
    ldb list --query 'breed.type || !breed.type'
    ```
   
    Goal: include only annotations with "truthy" value under `breed.type`:
    ```
    ldb add ds:root --query 'breed.type && class == `cat`'
    ```
    
- **Combine query terms**
    
    Input: dataset where image objects have annotations with "class" JSON field:
    
    ```json
    {
      "class": "cat",
      "breed": {
        "type": "main-coon",
        "size": "large"
      }
    }
    ```
    
    JMESPATH allows for logical grouping of boolean terms with &&, || , !
    
    ```bash
    # quotes required here to shield &&
    ldb list --query 'class==`cat` && breed.size==`large`'  
    
    ```
    
    Another way to achieve the AND operation is to pipeline multiple `--query` or `--file` flags:
    
     ```bash
    # quotes required here to shield &&
    ldb list --query 'class==`cat`' --query 'breed.size==`large`'  
    
    ```
    
    
- **Simple check for class balance**
    
    Input: JSON annotation with object classes:
    
    ```json
    {
      "class": "cat",
    }
    ```
    
    Display cumulative class counts:
    
    ```bash
    # note backslashes around  literals
    ldb list -s --query 'class==`cat`' 
    ldb list -s --query 'class==`dog`' 
    ```
    
- TODO beta: **Examine objects where inference results differ between model runs**

    Normally, JMESPATH query operates within a particular annotation JSON – namely, the one attached to the object referenced. If an object is a part of some dataset, it will have the same annotation version it was assigned when last added. If an object is referenced from the index, by default it will have the latest annotation version indexed.
    
    However, sometimes we want to run a JMESPATH query *between* annotation versions of one object. This happens, for example, if we want to compare how some field (e.g. model prediction) has evolved between several annotations. LDB achieves this via `--vquery` flag that modifies JSON tree, prepending an annotation version as root.
    
    Input: dataset where two annotation versions were produced after running the model twice: 
    
    ```json
    Annotation example version 1:
    
    {
      "class": "ii",
      "inference": {
        "class": "i",
      }
    }
    
    Annotation example version 2:
    
    {
      "class": "ii",
      "inference": {
        "class": "ii",
      }
    }
    ```
    
    Goal: compare inference results between the two versions:
    
    ```bash
    ldb stage ds:model-run-difference
    ldb add ds:roman-numerals --vquery 'v1.inference.class != v2.inference.class'
    ```
   
    
- **Get objects with a given number of array members (JMESPATH function `length`)**
    
    Input: JSON annotation that may have several object instances:
    
    ```json
    {
    	"instances" : [
    	    {
    	       "label": "cat"
    	    },
    	    {
    	       "label": "dog"
    	    },
            {
    	       "label": "dog"
    	    }
       ]
    }
    ```
    
    Query: add objects with a given number of instances
    
    ```bash
    # note backquotes on literal
    ldb add --query 'length(instances) == `3`' 
    ```
    
- **Class balance statistics**

  Input: JSON annotation with a class name field
    
    ```json
    {
      "class": "cat",
      "breed": {
        "type": "main-coon",
        "size": "large"
      }
    }
    ```
    Desired: object count per class 
   
   ```bash
   ldb eval -j --query 'class' ds:pets | sort | uniq -c
     100 "cat"
     100 "dog"

   ```
    
- **Histogram printing for numeric parameter**
    
    Input: JSON annotation that may have several object instances in a dataset 
    
    ```json
    {
    	"instances" : [
    	    {
    	       "label": "cat"
    	    },
    	    {
    	       "label": "dog"
    	    },
            {
    	       "label": "dog"
    	    }
        ]
    }
    ```
    
    Desired: histogram for distribution of some numeric key across samples in dataset (uses external program **hist** from [bashplotlib](https://github.com/glamp/bashplotlib ))
    
    ```bash
    
    $ ldb eval -j ds:pets --query 'length(instances)'  | hist -n
    
     6| o          
     5| o          
     4| o   o     o
     3| o   o     o
     2| o   o     o
     1| o   o  o  o
       -----------
    ```
- **Statistics evaluation for numeric parameter**
    
    Input: JSON annotation that has some numeric field
    
    ```json
    {
      "img": {
        "height": 768,
        "width": 1024
      }
    }
    ```
    
    Desired: histogram for distribution of numeric key across samples in dataset (uses external program **hist** from [num](https://github.com/numcommand/num)) (requires GNU gawk, e.g. `brew install --build-from-source gawk`)
    
    ```bash
    
    ldb eval -j  ds:images --query 'img.height'  | grep -v null | num stddev median
    
     185.858
    ```
    
- **Query** **objects when keys can be null**
    
    Input: JSON annotation that may have several object instances, but existence of array is not guaranteed:
    
    ```json
    {
    	"instances" : [
    	    {
    	       "label": "cat"
    	    },
    	    {
    	       "label": "dog"
    	    },
            {
    	       "label": "mouse"
    	    }
        ]
    }
    ```
    
    Let us say we are interested in counting number of instances:
    
    ```bash
    # note backquotes for literal
    ldb add --query 'length(instances) == `3`' 
    ```
    
    If we run the above query over annotations where key "instances" is null, JMESPATH function `length()` will fail:
    
    ```bash
    
    $ ldb eval 'length(instances) == `3`' 18de96e5871380ce1594b55d906ca816
    
    ERROR: In function length(), invalid type for value: None, expected one of: ['string', 'array', 'object'], received: "null"
    ```
    
    To prevent this failure, we can add a check if key is not null:
    
    ```bash
    
    ldb add --query 'not_null(instances) && length(instances) == `3`' 
    ```
    
- **Isolate objects with a helper ML model:**
    
    Input: Dataset consisting of cat images.
    
    Output:  20 images most close in semantic meaning to "sitting cat".
    
    ```bash
    
    ldb add --pipe clip-text 'sitting cat' --limit 20
    
    ```
    

Advanced examples 

- **Array operations: indexing**, **slicing, flattening, projections, filters**
    
    Input: Annotation for object `id:0dc11270eb2c136b454859df4b472aed`:
    
    ```json
    {
    	"instances" : [
    	    {
    	       "label": [
    	  	      "cat",
    		        "dog"
    				  ]
    	    },
    	    {
    	        "label": "dog"
    	    },
            {
    	        "label": "mouse"
    	    }
       ]
    }
    ```
    
    Indexing:
    
    ```bash
     
    ldb eval 'instances[0]' id:0dc11270eb2c136b454859df4b472aed
    
    {
         "label": [
    		"cat",
    		"dog"
    	 ]
    }
    ```
    
    Slicing (python syntax start:step:stop):
    
    ```bash
     
    ldb eval 'instances[:2:]' id:0dc11270eb2c136b454859df4b472aed
    
    [
      {
        "label": [
          "cat",
          "dog"
        ]
      },
      {
        "label": "mouse"
      }
    ]
    ```
    
    Projection:
    
    ```bash
     
    ldb eval 'instances[1:].label' id:0dc11270eb2c136b454859df4b472aed
    
    [
      "dog",
      "mouse"
    ]
    ```
    
    Flattening + projection:
    
    ```bash
     
    ldb eval 'instances[*].label[]' id:0dc11270eb2c136b454859df4b472aed
    
    [
      "cat",
      "dog",
      "dog",
      "mouse"
    ]
    ```
    
    Filters:
    
    ```bash
     
    ldb eval 'instances[?contains(label,`cat`)]' id:0dc11270eb2c136b454859df4b472aed
    
    [
      {
        "label": [
          "cat",
          "dog"
        ]
      }
    ]
    ```
    
    Pipes (flattening and sequential filters):
    
    ```bash
     
    $ ldb eval 'instances[?contains(label,`dog`)] | [0] | label[?@==`cat`]' id:0dc11270eb2c136b454859df4b472aed
    
    [
       "cat"
    ]
    ```
    
- **Object transforms:  list, hash**
    
    Input: Annotation for object `id:18de96e5871380ce1594b55d906ca816`:
    
    ```json
    {
      "class": "cat",
      "breed": {
        "type": "main-coon",
        "size": "large"
      }
    }
    ```
    
    Multiselect hash:
    
    ```bash
     
    ldb eval '{class:class}' id:18de96e5871380ce1594b55d906ca816
    
    {
      "class": "cat"
    }
    ```
    
    Multiselect subexpression and value swap:
    
    ```bash
     
    ldb eval '{breed:breed.{type:size}}' id:18de96e5871380ce1594b55d906ca816
    
    {
      "breed": {
        "type": "large"
      }
    }
    ```
    
    Multiselect list:
    
    ```bash
     
    ldb eval '[class, breed]' id:18de96e5871380ce1594b55d906ca816
    
    [
      "cat",
      {
        "type": "main-coon",
        "size": "large"
      }
    ]
    ```
    
- **Comparing string against regular expression (LDB JMESPATH extension `regex`)**
    
    Input: Dataset consisting of random object images.
    
    ```json
    {
      "class": "airpods",
      "inference": {
        "class": "beats",
        "confidence": 0.7
      }
    }
    ```
    
    Query:
    
    ```bash
    # note use of backquotes
    ldb list --query 'regex(inference.class, `"^b.+s$"`)'
    ```
    
    LDB JMESPATH func: `regex`
    
- **Simple math operation (LDB JMESPATH extension `sub`)**
    
    Input: annotation for audio record
    
    ```json
    {
      "original_length": 3.774375,
      "segments": [
        {
          "start": 0.2267952733485195,
          "end": 0.390150911161731,
          "labels": [
            "Positive"
          ]
        },
        {
          "start": 1.2267952733485195,
          "end": 1.390150911161731,
          "labels": [
            "Negative"
          ]
        },
        {
          "start": 2.2267952733485195,
          "end": 2.390150911161731,
          "labels": [
            "Positive"
          ]
        }
      ]
    }
    ```
    
     Goal: calculate cumulative duration of "Positive" sections
    
    ```shell
    $ ldb eval --query 'sum(segments[?contains(labels, `Positive`)].sub(end, start))'
    $ ldb list --query 'sum(segments[?contains(labels, `Positive`)].sub(end, start)) > `0.3`'
    ```
- Built-in JMESPATH functions

   JMESPATH specification comes with a [vast array of built-in functions](https://jmespath.org/specification.html#built-in-functions) like abs, avg. ceil, contains, not_null, max, sort, and so forth. 
   
- **Full list of** **LDB-specific functions**
    
    LDB is bundled with several functions that extend JMESPATH built-ins:
    
    - `sub(array, scalar)` → array
    - `sub(scalar, scalar)` → scalar
    - `sub(array, array)` → array             # arrays must match in dimensions
    - `prod(array, scalar)` → array
    - `prod(array, array)` → array
    - `div(array, scalar)` → array
    - `div(array, array)` → array                                       # arrays must match in dimensions
    - `dotproduct(array, array)` → scalar                       # arrays must match in dimensions
    - `unique(array)` → vector                                             # input array is flattened
    - `regex(object, regex_query)` → boolean                 # rules of regex
    
- TODO: **Custom (user-defined) functions**
    
    Users can define custom functions for complex queries. 
    
    For example, a custom function can be coded that accepts coordinates of two bounding boxes and outputs the area of overlapping surface (in pixels).
