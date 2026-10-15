# manifest.json 说明

推理服务通过这个文件知道「有哪些模型、分别对应什么类目」。

由 `cv/common/export/to_onnx.py` 生成（`cv/dog` 与 `cv/cat` 各自导出时累积进同一个清单），
手写也可以，格式如下：

```json
{
  "models": [
    {
      "kind": "cat",
      "version": "v3",
      "onnx": "cat-v3.onnx",
      "labels": "cat-labels.json",
      "imageSize": 224,
      "mean": [0.485, 0.456, 0.406],
      "std": [0.229, 0.224, 0.225]
    },
    {
      "kind": "dog",
      "version": "v2",
      "onnx": "dog-v2.onnx",
      "labels": "dog-labels.json"
    }
  ]
}
```

## labels.json

下标即模型输出的类 id：

```json
[
  { "breedId": "b-bsh", "title": "英国短毛猫", "sci": "Felis catus", "species": "cat" },
  { "breedId": "b-sphynx", "title": "斯芬克斯猫", "sci": "Felis catus", "species": "cat" }
]
```

## 注意

- `mean` / `std` 必须与训练时的归一化一致，否则精度会无声下降。
- 版本号会写进 `RecognitionResult.modelVersion`，用于线上问题追溯。
- 该目录在 .gitignore 中（权重不入库），部署时以挂载或制品方式提供。
