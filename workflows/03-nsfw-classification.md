# Workflow 03 · NSFW Classification

> 用 [NudeNet](https://github.com/notAI-tech/NudeNet) 给图片**自动打成人内容标签**。
> 这是养号系统能"识别成人内容"的核心 —— 不是 sfw/nsfw 二分类，而是 18 种细粒度标签。

---

## NudeNet 18 个标签

| 标签 | 含义 | 用途 |
|---|---|---|
| `FEMALE_GENITALIA_COVERED` | 女性私处遮挡 | 软色情，可发 |
| `FEMALE_GENITALIA_EXPOSED` | 女性私处暴露 | 硬色情，X 平台需打 sensitive |
| `FEMALE_BREAST_COVERED` | 胸部遮挡 | 软色情 |
| `FEMALE_BREAST_EXPOSED` | 胸部暴露 | 软色情 / 硬色情边界 |
| `MALE_GENITALIA_COVERED` | 男性私处遮挡 | - |
| `MALE_GENITALIA_EXPOSED` | 男性私处暴露 | 硬色情 |
| `MALE_BREAST_EXPOSED` | 男性胸部 | sfw 通常 |
| `BUTTOCKS_COVERED` | 臀部遮挡 | 软色情 |
| `BUTTOCKS_EXPOSED` | 臀部暴露 | 软色情 / 硬色情 |
| `ANUS_COVERED` | - | - |
| `ANUS_EXPOSED` | - | 硬色情 |
| `FEET_COVERED` | 脚部遮挡 | sfw |
| `FEET_EXPOSED` | 脚部暴露 | 恋足圈非常重要 |
| `BELLY_COVERED` | - | sfw |
| `BELLY_EXPOSED` | - | sfw |
| `ARMPITS_COVERED` | - | sfw |
| `ARMPITS_EXPOSED` | - | sfw / 部分小众圈 |
| `FACE_FEMALE` | 女性脸 | 用于检测有没有正脸 |
| `FACE_MALE` | 男性脸 | - |

每个标签返回：`class`, `score` (0-1), `box` (bbox)。

---

## 安装

```bash
pip install nudenet
```

第一次 import 会自动下载模型（~80MB）。

---

## 基础用法

### 单图分类

```python
from nudenet import NudeDetector

detector = NudeDetector()
results = detector.detect("path/to/image.jpg")

print(results)
# [
#   {"class": "FEMALE_BREAST_EXPOSED", "score": 0.92, "box": [100, 200, 300, 400]},
#   {"class": "FACE_FEMALE", "score": 0.87, "box": [120, 50, 280, 180]},
# ]
```

### 批量

```python
from pathlib import Path

images = list(Path("downloads").glob("*.jpg"))
results = detector.detect_batch([str(p) for p in images], batch_size=8)

for img, res in zip(images, results):
    print(img.name, [(r["class"], round(r["score"], 2)) for r in res])
```

### 内容打码（可发布前的合规处理）

```python
detector.censor(
    "input.jpg",
    classes=["FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED", "ANUS_EXPOSED"],
    output_path="censored.jpg"
)
```

---

## 业务封装：分级评分

```python
from enum import Enum
from nudenet import NudeDetector

class ContentLevel(Enum):
    SAFE = 0           # 完全 sfw
    SUGGESTIVE = 1     # 暗示性 / 软色情（封面 / banner 用）
    EXPLICIT = 2       # 明确成人 / 部分裸露（feed 主力）
    HARDCORE = 3       # 硬色情，X 平台需 sensitive 标记

EXPLICIT_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "FEMALE_GENITALIA_COVERED",
    "MALE_GENITALIA_COVERED",
}

HARDCORE_LABELS = {
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}

SUGGESTIVE_LABELS = {
    "FEMALE_BREAST_COVERED",
    "BUTTOCKS_COVERED",
    "BELLY_EXPOSED",
    "ARMPITS_EXPOSED",
    "FEET_EXPOSED",
}

detector = NudeDetector()

def classify(image_path, threshold=0.5):
    results = detector.detect(image_path)
    classes = {r["class"] for r in results if r["score"] >= threshold}
    
    if classes & HARDCORE_LABELS:
        return ContentLevel.HARDCORE
    if classes & EXPLICIT_LABELS:
        return ContentLevel.EXPLICIT
    if classes & SUGGESTIVE_LABELS:
        return ContentLevel.SUGGESTIVE
    return ContentLevel.SAFE
```

---

## 反向用法：识别**非**成人内容

养号过程中需要 sfw 内容做"伪装"（生活化推文 / banner），用相同模型反向筛选：

```python
def is_truly_safe(image_path):
    """所有可疑标签都低于 0.3 才算 sfw"""
    results = detector.detect(image_path)
    return all(r["score"] < 0.3 for r in results)
```

---

## 性能

| 模式 | 速度 | 备注 |
|---|---|---|
| CPU 单张 | ~150ms | 够用 |
| CPU batch (8) | ~80ms / 张 | 推荐 |
| GPU (CUDA) | ~10ms / 张 | 大规模建议 |
| ONNX runtime | ~50ms / 张 | 平衡 |

NudeNet 默认就是 ONNX，零配置即可。

---

## 入库示例

```python
import sqlite3, json
from nudenet import NudeDetector

conn = sqlite3.connect("media.db")
detector = NudeDetector()

def index_image(local_path):
    results = detector.detect(local_path)
    labels = json.dumps([{"class": r["class"], "score": r["score"]} for r in results])
    max_score = max((r["score"] for r in results), default=0)
    level = classify(local_path).value
    
    conn.execute(
        "INSERT INTO media_items (local_path, nsfw_labels, nsfw_max_score, content_level) VALUES (?, ?, ?, ?)",
        (local_path, labels, max_score, level)
    )
    conn.commit()
```

---

## 进阶：组合 + 文本审核

仅靠图片不够，X 平台也看推文文字。建议加一层文本审核：

```python
# 用 HuggingFace 的 unbiased-toxic-roberta 或 detoxify
from detoxify import Detoxify
text_model = Detoxify("original")

def is_text_safe(text):
    scores = text_model.predict(text)
    return scores["sexual_explicit"] < 0.7  # 阈值可调
```

把图 + 文同时过审，再决定是否发布 / 是否打 sensitive 标。

---

## ✅ 完成标志

- [ ] NudeNet 已 `pip install nudenet` 装好
- [ ] 媒体库的图都打过 4 级标签
- [ ] 数据库 `media_items.content_level` 字段填充完毕
- [ ] 发布池按等级分桶（SAFE / SUGGESTIVE / EXPLICIT / HARDCORE）

完成后进入 [04-warmup-loop.md](./04-warmup-loop.md)。
