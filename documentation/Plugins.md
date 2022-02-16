LDB supports pluggable executables that can be used to select data objects based on some operations over their annotations or binary content.

- Bundled plugin: [CLIP](#clip)
- Bundled plugin: [ResNet](#resnet)
- [Custom plugins](#custom-plugins)

## CLIP

OpenAI's [CLIP](https://github.com/openai/CLIP) is a popular semantic embedding model. Input images are embedded into semantic space, and compared by cosine similarity to an exemplar image or text string. 

To install:
```
cd ldb
pip install '.[clip-plugin]'
```
LDB clip plugin supports two ways to call: 

1. Using exemplar image.

```
clip-image <image_file_path> [<model_name>]
```

Where `model_name` is one of `RN50, RN101, RN50x4, RN50x16, RN50x64, ViT-B/32, ViT-B/16, ViT-L/14`

Examples:

```
ldb list ds:root --pipe clip-image ~/dogs-and-cats/cat.1000.jpg --limit 10
ldb list ds:root --pipe clip-image ~/dogs-and-cats/cat.1000.jpg RN50 --limit 10
```
2. Using exemplar text

```
clip-text <text_to_compare> [<model_name>]
```

Examples:

```
ldb list ds:root --pipe clip-text 'an orange cat' --limit 10
ldb list ds:root --pipe clip-text 'an orange cat' RN50 --limit 10

```


## ResNet

ResNet plugin sorts incoming image objects by cosine similarity on features from ["Deep Residual Network for Image Recognition"](https://arxiv.org/abs/1512.03385).

To install:
```
cd ldb
pip install '.[resnet-plugin]'
```

To call:
```
resnet-image <image_file_path> [<model_num> [<layer_num>]]
```
where `model_num` is one of `18, 34, 101, 152`, and `<layer_num>` is number between 1-4. Not specifying a layer means comoaring on the final output.

Examples:

```
ldb list ds:root --pipe resnet-image ~/dogs-and-cats/cat.1000.jpg --limit 10 # final output of default (resnet18)
ldb list ds:root --pipe resnet-image ~/dogs-and-cats/cat.1000.jpg 50 --limit 10 # final output of resnet50
ldb list ds:root --pipe resnet-image ~/dogs-and-cats/cat.1000.jpg 50 2 --limit 10 # layer 2 output of resnet50 

```

## Custom Plugins

LDB supports custom plugins. For information how to write a plugin, please refer to [command summary](Command-summary.md#pipe-plugins)
