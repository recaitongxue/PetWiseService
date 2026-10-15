# 狗品种识别模型 · 方法学与论文引用说明（Dog / THU-Dogs）

> 配套文件：`docs/references.bib`（BibTeX 引用键与本文一致）、`dog/configs/*`（可复现配置）。
> 所有**实测数字**来自 `artifacts/artifacts/eval-report-dog-test-full.*`（训练后生成），本文以【待补】占位。

## 1. 任务与数据集
- 任务：细粒度视觉分类（FGVC），对狗的品种进行 130 类识别。
- 数据集：**THU-Dogs** \cite{zou2020thudogs}：130 个品种、约 7 万张高分辨率图像；官方提供 `train.lst / val.lst / test.lst` 切分，且每图附带 **head / body 双 bbox 标注**。
- 长尾现象显著（多数类数千张、少数类仅百余张），是准确率的主要瓶颈之一。

## 2. 基线局限（写论文的"问题陈述"素材）
- 直接以 ResNet-50@224 + 普通交叉熵训练，验证集 Top-1 约 85%，但**尾部品种召回率接近 0%**、宏平均指标很低，说明"头部主导 + 长尾崩塌"。
- 改进方向：① 更强骨干与更高分辨率；② 抑制背景、聚焦目标的**bbox 裁剪**；③ 面向长尾的**类别均衡损失**；④ 强增强 + 现代训练配方。

## 3. 模型总体架构
- 骨干：**ConvNeXt-Large** \cite{liu2022convnet}（ImageNet-1k 预训练），输入分辨率 **384×384**。
  - 备选强骨干（同内核切换，便于消融）：Swin-B \cite{liu2021swin}、EfficientNet-V2-L \cite{tan2021efficientnetv2}、ViT-B/16 \cite{dosovitskiy2021an}、MaxViT-T \cite{tu2022maxvit}、ResNet-50 \cite{he2016deep}。
- 预处理：按 THU-Dogs 标注 **裁剪到 body bbox**（letterbox 等比补边，避免拉伸畸变），再 resize 到 384。
- 分类头：替换骨干末层线性层为 130 维全连接，随机初始化。

## 4. 核心方法——类别均衡 Focal 损失（本文创新点）
组合两篇经典工作，零额外参数、不增加推理成本，仅作用于训练：
- **Focal Loss** \cite{lin2017focal}：以 $(1-p_t)^\gamma$ 降低易分样本权重，聚焦难例；
- **Class-Balanced Loss** \cite{cui2019class}：以"有效样本数" $(1-\beta^{n_y})/(1-\beta)$ 对少数类加权，缓解长尾。

逐样本损失：
$$\mathcal{L}_{\text{cb\_focal}} = w_{y_i}\,(1-p_{y_i})^\gamma\,\ell_{\text{smooth}}(y_i,\hat y_i)$$
其中类别均衡权重 $w_c=\frac{1-\beta}{1-\beta^{n_c}}$（$\beta=0.9999$），$\gamma=2.0$，并兼容标签平滑 \cite{touvron2019fixres}。

> 可在"方法章"将其表述为：**针对 FGVC 长尾问题，提出以有效样本数为权重的类别均衡 Focal 损失，使优化聚焦难例与少数类，无需修改网络结构即可提升尾部识别。**

## 5. 训练策略（现代配方）
| 项 | 设置 | 依据 |
|---|---|---|
| 优化器 | AdamW，weight_decay=0.05 | \cite{liu2022convnet} |
| 学习率 | 1e-4（分类头 ×10） | 分层学习率 |
| 调度 | 线性预热 5 轮 + 余弦退火 | \cite{liu2021swin} |
| 增强 | RandAugment(2,9) \cite{cubuk2019randaugment} + RandomErasing | 强正则 |
| 损失 | 类别均衡 Focal | 本文创新 |
| EMA | decay=0.999（验证/保存/评测用 EMA 权重） | \cite{tarvainen2017mean} |
| 精度 | 混合精度(AMP) + DDP 双卡 + 梯度累积 | 工程 |
| bbox | body 裁剪 | THU-Dogs 标注 |

## 6. 评价指标（论文级，多维）
`common/eval/evaluate.py` 一次产出：Top-1/Top-5、宏/微/加权 Precision/Recall/F1、平衡准确率、Cohen's $\kappa$、ROC-AUC(OvR, macro)、**头/中/尾分段精度**、逐类召回（暴露 0% 类）、混淆矩阵（CSV+PNG）。

## 7. 消融实验设计（建议）
1. 骨干对比：ResNet-50 vs ConvNeXt-L vs Swin-B（同分辨率、同损失）→ 论证骨干贡献。
2. 损失对比：CE vs Focal vs **CB-Focal**（本文）→ 论证创新点。
3. bbox 裁剪：w/ vs w/o body 裁剪 → 论证定位增益。
4. 增强：w/ vs w/o RandAugment → 论证正则贡献。
5. 长尾增益：对比宏平均召回 / 尾部分段精度在 CE 与 CB-Focal 下的差异（核心卖点）。

## 8. 复现命令
```bash
cd cv && uv sync
bash scripts/prepare.sh dog          # 生成 labels-dog.json
bash scripts/train.sh dog            # 双 5090 自动 DDP → artifacts/artifacts/best-dog.pt
                                    #   + eval-report-dog-test-full.md / .json
bash scripts/export.sh dog           # 导出 dog.onnx
```
最终结果（Top-1/5、各分段精度、混淆矩阵）直接取自 `eval-report-dog-test-full.md`，回填本章第 8 节【待补】。

## 9. 引用键速查
`he2016deep`(ResNet) · `liu2022convnet`(ConvNeXt) · `liu2021swin`(Swin) · `tan2021efficientnetv2`(EffV2) · `dosovitskiy2021an`(ViT) · `tu2022maxvit`(MaxViT) · `lin2017focal`(Focal) · `cui2019class`(Class-Balanced) · `cubuk2019randaugment`(RandAug) · `cubuk2018autoaugment`(AutoAug) · `zhang2018mixup` · `yun2019cutmix` · `touvron2019fixres`(标签平滑) · `tarvainen2017mean`(EMA) · `fu2017look`/`wei2021weakly`(FGVC) · `zou2020thudogs`(数据集)。
