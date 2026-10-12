# 离线层：狗品种识别模型（THU-Dogs）

本目录**不对外提供任何端口**，它唯一的产物是一个 ONNX 权重文件，被 `services/vision` 只读加载。

```
cv/  ──训练+导出──▶  artifacts/model-dog-v1.onnx + labels-dog.json + manifest.json
                            │
                            └──只读挂载──▶  services/vision（在线推理）
```

边界很重要：训练代码可以随意重构，只要导出的契约（输入 `input`、输出 `logits`、224px、
ImageNet 归一化、labels 下标=类 id）不变，线上推理就不受影响。

## 数据集

用的是 **THU-Dogs**（清华大学犬种库），共 **130 类**，总计 ~7 万张。样本**极不均衡**：头部热门犬（泰迪/金毛/拉布拉多等）最多 7409 张，尾部稀有/工作犬每类仅 160 张、中位数 185 张——因此 `dataset.yaml` 默认开启 `balanced_sampling`（按类频反比加权），否则模型会被头部品种淹没。
目录布局（`datasets/`，已被 .gitignore）：

```
datasets/
├── high-resolution/<BREED>/<img>.(jpeg|jpg)            # 原图
├── high-annotations/<BREED>/<img>.(jpeg|jpg).xml       # 含 headbndbox / bodybndbox
└── TrainAndValList/
    ├── train.lst                                      # 65228 行，相对路径，含 \r
    ├── validation.lst                                 # 5200 行（官方原始划分，保留作回退）
    ├── val.lst                                        # 切分生成 2600 行（早停/选模型用）
    └── test.lst                                       # 切分生成 2600 行（独立评测用，训练全程不读）
```

> **关于测试集**：官方 THU-Dogs 只发 train + validation，没有 test。若把 validation
> 同时用于「早停选模型」和「最终报指标」，分数会偏乐观。因此 `prepare.sh` 第一步会调用
> `scripts/split_test.py`，按**每类确定性切分**（默认各 20/类 → val 2600 / test 2600，
> 固定 seed 可复现）生成 `val.lst` 与 `test.lst`。训练早停用 val、最终评测跑 test，
> 指标才真实可信。原始 `validation.lst` 不动，随时可回退。

`BREED` 形如 `1043-n000001-Shiba_Dog`，其中 `n000001` 是稳定品种码，用于生成 `breedId`。
**关键优势**：THU-Dogs 自带 head + body 双框标注，训练时裁到 body 框能去掉背景噪声、
显著提升分类准确率——这是本项目相对"直接拿 ImageNet 预训练分类头"的差异化点。

## 在 GPU 服务器上训练（推荐流程）

本地无 GPU 也没关系，代码在服务器上一条命令跑通：

```bash
# 0. 准备环境（服务器，建议 CUDA 12 + torch 2.x）
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. 生成 labels.json（只需 CPU，秒级；类别下标与训练强一致）
bash scripts/prepare.sh

# 2. 训练（AMP + 余弦退火 + 早停 + 断点续训）
#    best.pt 落在 artifacts/，训练曲线在 artifacts/train-history.csv
bash scripts/train.sh
#    断点续训：bash scripts/train.sh --resume artifacts/best.pt
#    只评测不训练：bash scripts/train.sh --only-eval

# 3. 导出 ONNX（services/vision 直接加载）
bash scripts/export.sh --kind dog --version v1
```

导出后在 `artifacts/` 得到 `model-dog-v1.onnx`、`labels-dog.json`、`manifest.json`，
把 `artifacts/` 整个目录挂到 `services/vision` 的 `ARTIFACTS_DIR` 即可上线。

## 切换骨干 / 调参（只改 yaml，不动代码）

`configs/train.yaml`：

```yaml
model:
  backbone: resnet50        # resnet50 | efficientnet_b3 | efficientnet_b4 | swin_t | convnext_tiny
  num_classes: 130          # 仅作校验：run.py 会断言其与数据集实际类数一致
  epochs: 40
  lr: 0.0003
  label_smoothing: 0.1      # 与 mixup/cutmix 互斥：启用任一时自动关闭
  mixup: 0.2                 # >0 开启 Mixup（长尾数据增强）；与 cutmix 二选一
  cutmix: 0.0                # >0 开启 CutMix；同时>0 时优先 cutmix
```

`configs/dataset.yaml` 是数据参数的唯一来源（**改这里就能切换数据集位置，无需动代码**）：

```yaml
dataset:
  root: datasets            # 原始数据根目录（相对 cv/ 或绝对路径）；Docker 挂载不同盘时改这一行即可
  image_size: 224
  use_bbox: true            # 用 body 框裁剪去背景；关掉即通用分类基线，方便做消融对比
  seed: 42                  # 随机种子，保证类平衡采样可复现
  balanced_sampling: true   # 类平衡采样（长尾必需）
  classes: []               # 类白名单（MVP 只训头部常见犬时填入品种文件夹名列表，如 ["1043-n000001-Shiba_Dog", ...]）
  test_split: true          # 把 validation.lst 切为 val.lst(早停)+test.lst(评测)；关掉则只用 validation.lst
  test_ratio: 0.5           # val 占比，剩余归 test（默认每类 20/20）
```

命令行 `--root <路径>` 仅用于**覆盖** `dataset.root`（比如把数据挂到别的盘），不传则一律以 yaml 为准。

## 长尾与拒识（业务注意）

- **长尾**：仅靠类平衡采样不足以让 92 个尾部稀有犬达到高召回，建议结合更强骨干 + Mixup。
- **拒识**：本模型**只训练了犬种**，没有猫/其它宠物的负样本。线上 `services/vision` 在
  top-1 置信度低于 `REJECT_THRESHOLD`（默认 0.5）时会返回「未识别到犬种」（`isUnknown=true`），
  **不会**把猫或模糊图强行认成某狗种——这是「宠物识别」可信度的底线。要真正支持猫，
  需另行训练猫模型或加负样本拒识类（见 docs/FEATURE-ROADMAP.md）。

## 目录说明

```
cv/
├── configs/           超参与数据配置（改实验只改这里）
├── src/
│   ├── data/
│   │   ├── annotation.py       THU-Dogs XML 解析（head/body 框）
│   │   ├── thudogs_meta.py     纯解析（不依赖 torch）：lst、扩展名容错、类别映射、labels
│   │   ├── thudogs.py          torch Dataset / DataLoader / bbox 裁剪
│   │   ├── make_labels.py      生成 labels.json 的 CLI
│   │   └── breed_cn.json       130 类中文名映射（可补充）
│   ├── models/factory.py       骨干 + 分类头组装（单一事实源）
│   ├── train/                  训练循环（run.py 入口 + trainer.py）
│   ├── eval/                   评测与 Markdown 报告
│   └── export/to_onnx.py       ONNX 导出（离线→在线的唯一交接点）
├── notebooks/          探索性实验，禁止进流水线
├── scripts/           prepare / train / export 三个入口
├── datasets/          数据集（gitignore）
└── artifacts/         权重与产物（gitignore）
```

## 三条纪律

1. **notebooks 是草稿**。确认有效的逻辑必须重写进 `src/`，否则无法复现。
2. **改 `normalize` / `image_size` 必须同步** `services/vision` 的 `preprocess.py` 与 `manifest.json`，
   否则会出现"离线指标好看、线上识别很差"。
3. **每次导出带版本号**（`model-dog-v1.onnx`），并与 `RecognitionResult.modelVersion` 对齐，方便回滚。
