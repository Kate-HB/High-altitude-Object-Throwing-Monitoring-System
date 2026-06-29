# YOLO 训练迁移到其他电脑流程

## 1. 迁移目标

把本机已整理好的高空抛物 YOLO 数据集和训练命令，迁移到 RTX 5060 Ti 台式机上继续训练。

迁移对象：

```text
data/falling_object/        # 完整数据集（含正负样本）
models/yolo11n.pt           # 预训练权重
scripts/check_yolo_env.py   # 环境检查脚本
scripts/prepare_dataset.py  # 数据集准备脚本（可选）
docs/YOLO训练到系统接入说明.md
```

不需要迁移：

```text
frontend/
backend/
uploads/
outputs/
events/
logs/
runs/
.venv/
.venv-labelimg/
```

## 2. 本机打包

在项目根目录执行（PowerShell）：

```powershell
Compress-Archive `
  data\falling_object,models\yolo11n.pt,scripts\check_yolo_env.py `
  yolo-training-package.zip -Force
```

如果要带说明文档：

```powershell
Compress-Archive `
  data\falling_object,models\yolo11n.pt,scripts\check_yolo_env.py,scripts\prepare_dataset.py,docs\YOLO训练到系统接入说明.md `
  yolo-training-package.zip -Force
```

> 注意：当前数据集约 1058 张图片（858 train + 200 val），压缩包约 300-500MB。

## 3. 传到另一台电脑

局域网、U盘、网盘都可以。

如果是云服务器：

```powershell
scp yolo-training-package.zip root@服务器IP:/root/yolo-train/
```

## 4. 目标电脑环境准备（Windows + RTX 5060 Ti）

### 4.1 确认 CUDA 环境

RTX 5060 Ti 需要 CUDA 12.4+。先确认驱动已安装：

```powershell
nvidia-smi
```

正常输出应显示 `NVIDIA GeForce RTX 5060 Ti`，CUDA Version 12.4 或更高。

### 4.2 安装 Conda（推荐）

Conda 管理 PyTorch CUDA 版本比 pip 更省心。下载 Miniconda：

```text
https://docs.anaconda.com/miniconda/
```

安装后打开 Anaconda Prompt（以管理员身份）。

```bash
conda create -n yolo python=3.10 -y
conda activate yolo
```

### 4.3 安装 PyTorch（CUDA 版）

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

验证 CUDA 可用：

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

必须输出：

```text
True
NVIDIA GeForce RTX 5060 Ti
```

### 4.4 安装 ultralytics 和 OpenCV

```bash
pip install ultralytics opencv-python
```

### 4.5 OMP 冲突处理（Windows 特有）

Windows 上 PyTorch 和 OpenCV 可能同时加载 `libiomp5md.dll`，导致 OMP Error #15 崩溃。设置环境变量：

```powershell
# 每次训练前执行（PowerShell）
$env:KMP_DUPLICATE_LIB_OK=1
```

或者在系统环境变量中永久添加：
- 变量名：`KMP_DUPLICATE_LIB_OK`
- 变量值：`1`

## 5. 解压数据

Windows（PowerShell）：

```powershell
Expand-Archive yolo-training-package.zip -DestinationPath . -Force
```

Linux：

```bash
unzip yolo-training-package.zip -d .
```

解压后应有：

```text
data/falling_object/images/train/     # 训练图片（858 张）
data/falling_object/images/val/       # 验证图片（200 张）
data/falling_object/labels/train/     # 训练标签（858 个，含 98 个空标签=负样本）
data/falling_object/labels/val/       # 验证标签（200 个，含 17 个空标签=负样本）
data/falling_object/data.yaml
models/yolo11n.pt
scripts/check_yolo_env.py
```

## 6. 检查数据集完整性

在项目根目录执行：

Windows（PowerShell）：

```powershell
$trainImg = (Get-ChildItem data\falling_object\images\train | Measure-Object).Count
$trainLbl = (Get-ChildItem data\falling_object\labels\train | Measure-Object).Count
$valImg   = (Get-ChildItem data\falling_object\images\val   | Measure-Object).Count
$valLbl   = (Get-ChildItem data\falling_object\labels\val   | Measure-Object).Count

Write-Host "train: $trainImg images / $trainLbl labels  (应为 858/858)"
Write-Host "val:   $valImg images / $valLbl labels    (应为 200/200)"
```

Linux：

```bash
echo "train:" $(ls data/falling_object/images/train | wc -l) "images /" $(ls data/falling_object/labels/train | wc -l) "labels"
echo "val:  " $(ls data/falling_object/images/val | wc -l) "images /" $(ls data/falling_object/labels/val | wc -l) "labels"
```

检查标准：

```text
图片数 = 标签数（一一对应）
data.yaml 中 path 路径正确
data.yaml 中 names 只有 falling_object
```

### 6.1 验证图片标签匹配（推荐）

Linux / Git Bash：

```bash
cd data/falling_object
for f in labels/train/*.txt; do
  base=$(basename "$f" .txt)
  if [ ! -f "images/train/$base.jpg" ] && [ ! -f "images/train/$base.JPG" ] && [ ! -f "images/train/$base.png" ]; then
    echo "ORPHAN label: $f"
  fi
done
echo "以上无输出则通过"
```

### 6.2 确认 data.yaml

```yaml
path: data/falling_object
train: images/train
val: images/val
names:
  0: falling_object
```

注意：`path` 是相对于项目根目录的路径。如果解压到不同位置，需要修改 `path` 为绝对路径，如：

```yaml
path: D:/yolo-train/data/falling_object
```

## 7. 训练命令

### 7.1 RTX 5060 Ti（8GB）推荐命令

```powershell
$env:KMP_DUPLICATE_LIB_OK=1
yolo train model=models/yolo11n.pt data=data/falling_object/data.yaml epochs=60 batch=24 imgsz=640 device=0 workers=4 cache=true optimizer=AdamW lr0=0.001 lrf=0.01 patience=15 close_mosaic=10 box=10.0 cls=0.8 project=runs/train name=falling_object_yolo11n_v2
```

| 参数 | 说明 |
|------|------|
| `batch=24` | 5060 Ti 8GB 推荐。16GB 显存可调至 48 |
| `epochs=60` | 当前数据集 45 轮左右收敛，60 轮留余量 |
| `workers=4` | 数据加载并行数（6-8 核 CPU 用 4） |
| `cache=true` | 首次训练缓存图片到内存，后续 epoch 更快 |
| `patience=15` | 15 轮无改善则早停 |
| `close_mosaic=10` | 最后 10 轮关闭 mosaic 增强，稳定收敛 |
| `box=10.0` | 提高边界框回归损失权重（默认 7.5），改善定位 |
| `cls=0.8` | 提高分类损失权重（默认 0.5），降低误检 |
| `lr0=0.001 lrf=0.01` | 初始学习率和最终学习率比例 |

### 7.2 如果爆显存

```text
batch=16
batch=12
batch=8
```

RTX 5060 Ti 8GB 上 yolo11n + imgsz=640 的 batch=24 通常不会爆。如果同时有其他进程占显存，降到 16。

### 7.3 RTX 5060 Ti（16GB）命令

```powershell
yolo train model=models/yolo11n.pt data=data/falling_object/data.yaml epochs=60 batch=48 imgsz=640 device=0 workers=6 cache=true optimizer=AdamW lr0=0.001 lrf=0.01 patience=15 close_mosaic=10 box=10.0 cls=0.8 project=runs/train name=falling_object_yolo11n_v2
```

### 7.4 纯 CPU 训练（无 GPU 方案）

```bash
yolo train model=models/yolo11n.pt data=data/falling_object/data.yaml epochs=60 batch=8 imgsz=320 device=cpu workers=0 optimizer=AdamW lr0=0.001 lrf=0.01 patience=15 close_mosaic=10 project=runs/train name=falling_object_yolo11n_cpu
```

极其慢，仅作应急。

## 8. 训练过程监控

### 8.1 实时 GPU 使用

```powershell
nvidia-smi -l 1
```

正常现象：

```text
python 进程占用 GPU
GPU-Util: 80-100%（正常满载）
Memory: 取决于 batch 大小
温度: 60-80°C
```

如果 GPU-Util 只有 20-50%：
- `workers=4` 太低，提高
- `batch` 可以再加大
- 检查是否有其他程序占用 GPU

### 8.2 终端输出关注指标

```text
Epoch    当前轮数
GPU_mem  GPU 显存占用
box_loss 边界框损失（越低越好）
cls_loss 分类损失（越低越好）
dfl_loss 分布焦点损失（越低越好）
Precision 精确率（防误检，越高越好）
Recall    召回率（防漏检，越高越好）
mAP50     IoU0.5 平均精度（核心指标）
mAP50-95  IoU0.5-0.95 平均精度（定位指标）
```

### 8.3 训练曲线判断

```text
mAP50 在上升         → 正常，继续
mAP50 走平 >15轮     → 早停触发，可以结束
val/loss 持续上升     → 过拟合，需要早停或加数据
P高 R低（差值>10%）   → 误检少但漏检多，降低 cls 损失权重
P低 R高（差值>10%）   → 误检多但漏检少，提高 cls 损失权重
```

### 8.4 查看训练结果图表

训练完成后在 `runs/train/falling_object_yolo11n_v2/` 查看：

```text
results.png              # 所有训练曲线汇总
confusion_matrix.png     # 混淆矩阵（TP/FP/FN 数值）
BoxPR_curve.png          # PR 曲线
val_batch*_pred.jpg      # 验证集预测可视化
```

## 9. 创建验证集（可选）

如果想用脚本自动划分训练/验证集：

```bash
python scripts/prepare_dataset.py --split-val 200
```

### 9.1 手动划分

按比例随机移动：

Linux / Git Bash：

```bash
cd data/falling_object
# 从训练集随机移动 N 张到验证集
find images/train -type f | shuf -n 200 | while read f; do
  base=$(basename "$f")
  name="${base%.*}"
  mv "images/train/$base" "images/val/"
  mv "labels/train/$name.txt" "labels/val/"
done
```

### 9.2 负样本处理

负样本（无目标的背景图）需要建立空标签文件：

```bash
# 为负样本图片创建空标签
for img in images/train/neg_*.jpg; do
  base=$(basename "$img" .jpg)
  touch "labels/train/$base.txt"
done
```

## 10. 训练完成后取回权重

最佳权重在：

```text
runs/train/falling_object_yolo11n_v2/weights/best.pt
```

复制为系统模型名：

Windows：

```powershell
Copy-Item runs\train\falling_object_yolo11n_v2\weights\best.pt models\falling_object_yolo11n.pt -Force
```

Linux：

```bash
cp runs/train/falling_object_yolo11n_v2/weights/best.pt models/falling_object_yolo11n.pt
```

云服务器下载回本机：

```powershell
scp root@服务器IP:/root/yolo-train/runs/train/falling_object_yolo11n_v2/weights/best.pt models\falling_object_yolo11n.pt
```

## 11. 验证权重

图片验证：

```bash
yolo detect predict model=models/falling_object_yolo11n.pt source=data/falling_object/images/val imgsz=640 conf=0.25 save=True
```

视频验证：

```bash
yolo detect predict model=models/falling_object_yolo11n.pt source=data/videos/demo.mp4 imgsz=640 conf=0.25 save=True
```

推荐的推理置信度：

```text
conf=0.5   生产环境推荐（平衡误检和漏检）
conf=0.25  展示用，召回优先（允许更多误检）
conf=0.6+  高精度需求，误检容忍度低
```

## 12. 接回本机系统

把训练好的权重放到项目 `models/` 目录：

```text
models/falling_object_yolo11n.pt
```

后续算法 Pipeline 加载：

```python
from ultralytics import YOLO
model = YOLO("models/falling_object_yolo11n.pt")
```

不要提交到 Git：

```text
*.pt
data/
runs/
outputs/
logs/
```

已在 `.gitignore` 中配置。

## 13. 常见问题

### 13.1 `cuda_available=false`

当前 PyTorch 不是 CUDA 版，或驱动不匹配。

检查：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

处理：重新安装 CUDA 版 PyTorch：

```bash
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### 13.2 `OMP: Error #15`（Windows 特有）

```text
OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
```

处理：

```powershell
$env:KMP_DUPLICATE_LIB_OK=1
```

或在系统环境变量永久添加 `KMP_DUPLICATE_LIB_OK=1`。

### 13.3 `CUDA out of memory`

处理顺序：

```text
batch 降低（24 → 16 → 12 → 8）
imgsz 降低到 480
关闭浏览器等其他占 GPU 程序
关闭训练以外的所有 Python 进程
```

### 13.4 路径错误 `'data/falling_object/data.yaml' does not exist`

说明不是在项目根目录执行的命令。先 `cd` 到项目根目录。

### 13.5 训练结果目录嵌套

如果出现：

```text
runs/detect/runs/train/...
```

不影响训练，只是启动命令所在目录有问题。最终权重在 `weights/best.pt`。

### 13.6 `ModuleNotFoundError: No module named 'torch'`

说明没激活 conda 环境：

```bash
conda activate yolo
```

### 13.7 标签不匹配

验证集结果全部为 0（mAP=0）：

- 检查 `data.yaml` 中 `path` 是否指向正确目录
- 检查 label 文件是否存在且格式正确（YOLO 格式：`class_id x_center y_center width height`）
- 检查空标签（负样本）文件是否存在

### 13.8 训练中中断恢复

```bash
yolo train model=runs/train/falling_object_yolo11n_v2/weights/last.pt data=data/falling_object/data.yaml resume=True
```
