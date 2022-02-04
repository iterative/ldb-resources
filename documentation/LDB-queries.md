# Query examples

LDB uses [JMESPATH](https://jmespath.org/specification.html) as a query language over JSON annotations. This allows for complicated data selection and statistics that would normally require custom programming.

The way LDB treats JMESPATH expressions is as follows:

- All query-enabled commands expand the provided list of objects and evaluate JMESPATH over annotations one-by-one.
- **ADD**, **DEL**, **LIST** evaluate the result of JMESPATH as true/false – which determines whether an object is selected for processing. Rules for "falsy" evaluation are as follows: `boolean false, null, empty object, empty list, empty string` (i.e. `[]`, `{}`, `""`, `false`, `null`). 
[Everything else, including `0` and `0.0` evaluates to `true`.](https://jmespath.org/specification.html#or-expressions)
- **EVAL** prints raw JMESPATH query output over annotations

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
    $ ldb add ds:root --query 'class == `cat`'
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
    $ ldb add ds:root --query 'inference.confidence >= `0.8`' 
    
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
    
    $ ldb add ds:root --query 'inference.class != class'
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
    $ ldb list --query 'inference == `{"confidence": 0.7, "class": "pro"}`'
    
    ```
    
- **Get objects where annotation includes certain key**
    
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
    
    Goal: print objects where annotations have a key evaluating to 
    
    ```bash
    # non-empty key is resolved to "true"
    $ ldb list --query breed.type
    
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
    $ ldb list --query 'class==`cat` && breed.size==`large`'  
    
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
    $ ldb list -s --query 'class==`cat`' 
    $ ldb list -s --query 'class==`dog`' 
    ```
    
- TODO beta: **Examine objects where inference results differ between model runs**
    
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
    
    ```bash
    $ ldb stage ds:model-run-difference
    $ ldb add ds:roman-numerals --query 'v1.inference.class != v2.inference.class'
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
    $ ldb add --query 'length(instances) == `3`' 
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
    
    Desired: histogram for distribution of numeric key across samples in dataset (uses external program **hist** form **bashplotlib**)
    
    ```bash
    
    $ ldb eval -q 'length(instances)' ds:pets | hist -n
    
     6| o          
     5| o          
     4| o   o     o
     3| o   o     o
     2| o   o     o
     1| o   o  o  o
       -----------
    ```
    
- **Query** **objects when keys can be absent**
    
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
    $ ldb add --query 'length(instances) == `3`' 
    ```
    
    If we run the above query over annotations that do not have array "instances", JMESPATH function `length()` will fail:
    
    ```bash
    
    $ ldb eval  'length(instances) == `3`' 0x18de96e5871380ce1594b55d906ca816
    
    ERROR: In function length(), invalid type for value: None, expected one of: ['string', 'array', 'object'], received: "null"
    ```
    
    To prevent this failure, we can add a check for key presence:
    
    ```bash
    
    $ ldb add --query 'instances && length(instances) == `3`' 
    ```
    
- **Isolate objects with a helper ML model:**
    
    Input: Dataset consisting of cat images.
    
    Output:  20 images most close in semantic meaning to "sitting cat".
    
    ```bash
    
    $ ldb add --pipe clip-text 'sitting cat' --limit 20
    
    ```
    

Advanced examples 

- **Array operations: indexing**, **slicing, flattening, projections, filters**
    
    Input: Annotation for object `0x0dc11270eb2c136b454859df4b472aed`:
    
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
     
    $ ldb eval 'instances[0]' 0x0dc11270eb2c136b454859df4b472aed
    
    {
         "label": [
    		"cat",
    		"dog"
    	 ]
    }
    ```
    
    Slicing (python syntax start:step:stop):
    
    ```bash
     
    $ ldb eval 'instances[:2:]' 0x0dc11270eb2c136b454859df4b472aed
    
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
     
    $ ldb eval 'instances[1:].label' 0x0dc11270eb2c136b454859df4b472aed
    
    [
      "dog",
      "mouse"
    ]
    ```
    
    Flattening + projection:
    
    ```bash
     
    $ ldb eval 'instances[*].label[]' 0x0dc11270eb2c136b454859df4b472aed
    
    [
      "cat",
      "dog",
      "dog",
      "mouse"
    ]
    ```
    
    Filters:
    
    ```bash
     
    $ ldb eval 'instances[?contains(label,`cat`)]' 0x0dc11270eb2c136b454859df4b472aed
    
    [
      {
        "label": [
          "cat",
          "dog"
        ]
      }
    ]
    ```
    
- **Object transforms:  list, hash**
    
    Input: Annotation for object `0x18de96e5871380ce1594b55d906ca816`:
    
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
     
    $ ldb eval '{class:class}' 0x18de96e5871380ce1594b55d906ca816
    
    {
      "class": "cat"
    }
    ```
    
    Multiselect subexpression and value swap:
    
    ```bash
     
    $ ldb eval '{breed:breed.{type:size}}' 0x18de96e5871380ce1594b55d906ca816
    
    {
      "breed": {
        "type": "large"
      }
    }
    ```
    
    Multiselect list:
    
    ```bash
     
    $ ldb eval '[class, breed]' 0x18de96e5871380ce1594b55d906ca816
    
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
    $ ldb list --query 'regex(inference.class, `"^b.+s$"`)'
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
    
- TODO: **Full list of** **LDB-specific functions**
    
    LDB is bundled with several functions that extend JMESPATH built-ins:
    
    - `sub(array, scalar)` → array
    - `sub (scalar, scalar)` → scalar
    - `sub (array, array)` → array             # arrays must match in dimensions
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
