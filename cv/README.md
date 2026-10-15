# PetWise · 宠物细粒度识别（猫 / 狗品种分类）

面向毕业设计的细粒度视觉分类（FGVC）训练框架。**狗**基于 [THU-Dogs](docs/references.bib)（130 类，含 head/body 双 bbox 标注），**猫**基于自建 60 类数据集。代码共用一套内核（`common/`），狗猫通过配置 + 数据适配区分。

## 设计要点（确保准确率）
- **强骨干**：狗 ConvNeXt-Large、猫 EfficientNet-V2-L（ImageNet 预训练），输入 **384×384**。内核可一键切换 Swin-B / ViT-B / MaxViT / ResNet-50。
- **自研损失（论文创新点）**：类别均衡 Focal 损失 = Focal \cite{lin2017focal} + 有效样本数类别均衡 \cite{cui2019class}，专治长尾 0% 召回。
- **bbox 裁剪**：狗用 THU-Dogs 的 body bbox + letterbox 等比补边，抑制背景、聚焦目标。
- **现代训练配方**：RandAugment + RandomErasing + 标签平滑 + EMA + 余弦退火 + 混合精度 + DDP 双卡 + 梯度累积 + TTA 评测。
- **论文级指标**：Top-1/5、宏/微/加权 P-R-F1、平衡准确率、Cohen's κ、ROC-AUC(OvR)、头/中/尾分段精度、混淆矩阵。

## 目录结构
```
cv/
├── common/                 # 共用内核（模型/数据/训练/评测）
│   ├── data/               # labels, bbox, dataset, transforms, sampler
│   ├── models/             # factory(强骨干) + loss(类别均衡Focal)
│   ├── train/              # engine(DDP/EMA/AMP) + cli(入口)
│   ├── eval/               # 论文级多维评测
│   └── export/             # ONNX 导出
├── dog/configs/            # 狗：dataset.yaml + train.yaml (convnext_large + bbox)
├── cat/configs/            # 猫：dataset.yaml + train.yaml (efficientnet_v2_l)
├── scripts/                # prepare / train / export
├── docs/                  # references.bib + methodology_dog.md（论文可直接引用）
├── datasets/              # 原始数据（THU-Dogs / 猫）
└── artifacts/artifacts/    # 标签、权重、评测报告（训练产物）
```

## 环境
- Python ≥ 3.11，需要 **NVIDIA GPU**（`uv.lock` 含 CUDA 12/13 依赖）。本框架在双 RTX 5090（64GB）验证设计。
- 安装：`cd cv && uv sync`

## 快速开始（狗识别，论文主实验）
```bash
cd cv && uv sync
bash scripts/prepare.sh dog        # 生成 artifacts/artifacts/labels-dog.json（130 类）
bash scripts/train.sh dog          # 自动检测多卡 → torchrun DDP，默认 configs/train.yaml
# 产物：artifacts/artifacts/best-dog.pt + eval-report-dog-test-full.md / .json
bash scripts/export.sh dog         # 导出 artifacts/artifacts/dog.onnx
```
仅评测已有权重：`bash scripts/train.sh dog --only-eval`

## 猫识别
```bash
bash scripts/prepare.sh cat
bash scripts/train.sh cat
bash scripts/export.sh cat
```

## 论文素材
- `docs/references.bib`：可直接 `\bibliography{references}` 的 BibTeX（含 THU-Dogs 数据集引用）。
- `docs/methodology_dog.md`：方法章节草稿（技术→文献映射、损失公式、消融设计、复现命令）。

## ⚠️ 上线纪律
`image_size` 在 `dog/cat/configs/dataset.yaml` 中统一为 384，**线上推理服务须使用相同的 384 预处理**，否则会出现 train/serve 偏差（离线指标虚高、线上骤降）。导出脚本已自动读取该值。

## 关键引用
ResNet \cite{he2016deep} · ConvNeXt \cite{liu2022convnet} · Swin \cite{liu2021swin} · EfficientNetV2 \cite{tan2021efficientnetv2} · ViT \cite{dosovitskiy2021an} · Focal \cite{lin2017focal} · Class-Balanced \cite{cui2019class} · RandAug \cite{cubuk2019randaugment} · EMA \cite{tarvainen2017mean} · THU-Dogs \cite{zou2020thudogs}。
