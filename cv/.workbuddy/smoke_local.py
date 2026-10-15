"""本机 CPU 冒烟校验：不跑 GPU 训练，仅验证代码链路无接口/逻辑错误。
覆盖：标签构建、bbox 解析与 letterbox、THU-Dogs/猫数据集加载、强骨干构造（头替换）、
类别均衡 Focal 损失、分布式类平衡采样、论文级评测（sklearn 路径 + 报告写出）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ok = []

# 1) 标签构建
from common.data import labels as L
art = ROOT / "artifacts" / "artifacts"
art.mkdir(parents=True, exist_ok=True)
for kind in ("dog", "cat"):
    lab = L.build_labels(kind, ROOT / "datasets" / kind, art)
    print(f"[labels] {kind}: {lab['num_classes']} 类")
    ok.append(("labels", kind, lab["num_classes"]))

# 2) bbox 解析 + letterbox
from common.data import bbox as B
from PIL import Image
xml = next((ROOT / "datasets/dog/high-annotations/1043-n000001-Shiba_Dog").glob("*.xml"))
boxes = B.parse_annotation(xml)
print(f"[bbox] head={boxes['head']} body={boxes['body']}")
assert boxes["body"] is not None
img = Image.new("RGB", (720, 720), (120, 120, 120))
crop = B.letterbox_crop(img, boxes["body"])
print(f"[bbox] letterbox crop size={crop.size}")
ok.append(("bbox", "letterbox", crop.size[0]))

# 3) 数据集加载（狗 + 猫）
from common.data.transforms import build_transforms
from common.data.dataset import build_dataset
tf = build_transforms(384, train=True, use_bbox=True)
dog_ds_cfg = {"dataset": L.load_dataset_yaml(ROOT / "dog/configs/dataset.yaml")}
ds = build_dataset("dog", "train", dog_ds_cfg, art, tf)
print(f"[dataset:dog] train 样本数={len(ds)}")
im, lb = ds[0]
print(f"[dataset:dog] 单样本 img={tuple(im.shape)} label={lb}")
assert im.shape == (3, 384, 384)
ok.append(("dataset", "dog", len(ds)))

# 猫（无 bbox）
cat_ds = L.load_dataset_yaml(ROOT / "cat/configs/dataset.yaml")
cat_ds["root"] = str(ROOT / "datasets" / "cat")
catcfg = {"dataset": cat_ds}
tf_cat = build_transforms(384, train=True, use_bbox=False)
ds_cat = build_dataset("cat", "train", catcfg, art, tf_cat)
imc, lbc = ds_cat[0]
print(f"[dataset:cat] 单样本 img={tuple(imc.shape)} label={lbc}")
assert imc.shape == (3, 384, 384)
ok.append(("dataset", "cat", len(ds_cat)))

# 4) 强骨干构造（头替换，pretrained=False 避免下载）
from common.models import factory as F
for bb in ("resnet50", "convnext_large", "swin_b", "efficientnet_v2_l", "vit_b_16", "maxvit_t"):
    m = F.build_model(bb, 130, pretrained=False)
    # 取分类头输出维
    if bb.startswith("resnet"):
        out = m.fc.out_features
    elif bb.startswith("convnext") or bb.startswith("efficientnet") or bb.startswith("maxvit"):
        out = m.classifier[-1].out_features
    elif bb.startswith("swin"):
        out = m.head.out_features
    else:  # vit
        out = m.heads.out_features if hasattr(m.heads, "out_features") else m.heads[-1].out_features
    print(f"[factory] {bb}: 分类头输出={out}")
    assert out == 130
ok.append(("factory", "all", 130))

# 5) 类别均衡 Focal 损失
import torch
from common.models.loss import build_criterion
crit = build_criterion("cb_focal", 130, class_counts=[10] * 130, label_smoothing=0.1, focal_gamma=2.0)
logits = torch.randn(8, 130)
targets = torch.randint(0, 130, (8,))
loss = crit(logits, targets)
print(f"[loss] cb_focal loss={float(loss):.4f}")
assert float(loss) > 0 and torch.isfinite(loss)
ok.append(("loss", "cb_focal", float(loss)))

# 6) 分布式类平衡采样（单卡）
from common.data.sampler import DistributedBalancedSampler, make_balanced_sampler
targets = [0] * 90 + [1] * 10 + [2] * 30
smp = DistributedBalancedSampler(targets, num_replicas=1, rank=0, alpha=0.5)
idxs = list(smp)
print(f"[sampler] 采样数={len(idxs)} (总样本={len(targets)})")
assert len(idxs) == len(targets)
ok.append(("sampler", "dist", len(idxs)))

# 7) 论文级评测（合成数据，走 sklearn 路径）
from common.eval import evaluate as EV
import numpy as np

class Synth(torch.utils.data.Dataset):
    def __len__(self):
        return 300
    def __getitem__(self, i):
        return torch.randn(3, 32, 32), i % 5

class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.f = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(3 * 32 * 32, 5))
    def forward(self, x):
        return self.f(x)

model = Tiny().eval()
loader = torch.utils.data.DataLoader(Synth(), batch_size=32)
rep = EV.evaluate_full(model, loader, tta=False, class_names=[f"c{i}" for i in range(5)],
                       train_counts=[100, 50, 30, 20, 10], output_dir=art, split="test", kind="dog")
print("[eval] top1=", rep["top1"], "balancedAcc=", rep.get("balancedAccuracy"),
      "kappa=", rep.get("cohenKappa"), "seg=", rep.get("segmentAccuracy"))
assert rep["top1"] >= 0 and rep["balancedAccuracy"] is not None
ok.append(("eval", "full", rep["top1"]))

print("\n=== SMOKE_OK ===")
for o in ok:
    print("  ", o)
