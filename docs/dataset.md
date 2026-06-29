# 数据集目录说明

## 原始目录

```text
data/raw/
  images/        # 原始图片或抽帧图片
  labels/        # YOLO标注，文件名与图片一致
```

## 输出目录

```text
data/falling_object/
  images/train/
  images/val/
  labels/train/
  labels/val/
  classes.txt
  data.yaml
```

## 类别

统一单类别：

```text
0 falling_object
```

## 使用

```powershell
python scripts\prepare_dataset.py --source data\raw --output data\falling_object --val-ratio 0.2
```

抽帧：

```powershell
python scripts\prepare_dataset.py --source data\raw --output data\falling_object --video-dir data\videos --frame-step 10
```

## 样例标注

```text
0 0.500000 0.500000 0.200000 0.200000
```
