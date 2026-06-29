# 数据集来源记录

## 目标

为 YOLOv11 单类别 `falling_object` 准备高空抛物/坠物检测样本。

## 候选来源

| 来源 | 用途 | 状态 |
|---|---|---|
| 阿里云天池高空抛物数据集 | 主数据源，视频抽帧 | 需登录下载 |
| firc-dataset 高空抛物检测数据集 | 3000张，VOC+YOLO，6类别 | 可尝试获取 |
| Roboflow Object_Throwing | 抛掷物体检测 | 可导出YOLO，需账号 |
| 自录楼上抛物演示视频 | 课程演示正样本 | 可执行 |
| 无抛物监控片段 | 负样本 | 可执行 |

## 不采用

跌倒检测、人体 fall detection、普通垃圾检测、海洋垃圾检测，不符合高空抛物任务。

## 本地目录

```text
data/videos/
data/raw/images/
data/raw/labels/
data/falling_object/
```

## 类别

```text
0 falling_object
```

## 参考链接

- https://tianchi.aliyun.com/dataset/180178
- https://github.com/flsl/firc-dataset
- https://universe.roboflow.com/dataannotation-6yyxf/object_throwing
