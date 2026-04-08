"""
Example 02 · NudeNet Classify
=============================

NudeNet 自动给图片打 18 种成人内容标签，并按 4 级（SAFE / SUGGESTIVE / EXPLICIT / HARDCORE）入库。

依赖：
    pip install nudenet

文档：https://github.com/notAI-tech/NudeNet
"""

import argparse
import json
import sqlite3
import sys
from enum import IntEnum
from pathlib import Path

from nudenet import NudeDetector


class ContentLevel(IntEnum):
    SAFE = 0
    SUGGESTIVE = 1
    EXPLICIT = 2
    HARDCORE = 3


HARDCORE_LABELS = {
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}

EXPLICIT_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "FEMALE_GENITALIA_COVERED",
    "MALE_GENITALIA_COVERED",
}

SUGGESTIVE_LABELS = {
    "FEMALE_BREAST_COVERED",
    "BUTTOCKS_COVERED",
    "BELLY_EXPOSED",
    "ARMPITS_EXPOSED",
    "FEET_EXPOSED",
}


detector = NudeDetector()


def classify(image_path: str, threshold: float = 0.5) -> tuple[ContentLevel, list[dict]]:
    raw = detector.detect(image_path)
    classes = {r["class"] for r in raw if r["score"] >= threshold}
    if classes & HARDCORE_LABELS:
        level = ContentLevel.HARDCORE
    elif classes & EXPLICIT_LABELS:
        level = ContentLevel.EXPLICIT
    elif classes & SUGGESTIVE_LABELS:
        level = ContentLevel.SUGGESTIVE
    else:
        level = ContentLevel.SAFE
    return level, raw


def censor_if_hardcore(image_path: str, output_path: str) -> bool:
    """硬核内容打码后保存。返回是否被打码。"""
    raw = detector.detect(image_path)
    hardcore_present = [r["class"] for r in raw if r["class"] in HARDCORE_LABELS and r["score"] >= 0.5]
    if not hardcore_present:
        return False
    detector.censor(image_path, classes=list(HARDCORE_LABELS), output_path=output_path)
    return True


def init_db(db_path: str = "media.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_path TEXT UNIQUE NOT NULL,
            content_level INTEGER NOT NULL,
            nsfw_labels TEXT NOT NULL,
            max_score REAL NOT NULL,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def index_directory(image_dir: str, db_path: str = "media.db"):
    conn = init_db(db_path)
    paths = [p for p in Path(image_dir).rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    print(f"[*] indexing {len(paths)} images from {image_dir}")
    for p in paths:
        try:
            level, raw = classify(str(p))
            max_score = max((r["score"] for r in raw), default=0.0)
            labels_json = json.dumps([{"class": r["class"], "score": r["score"]} for r in raw])
            conn.execute(
                "INSERT OR REPLACE INTO media_items (local_path, content_level, nsfw_labels, max_score) VALUES (?, ?, ?, ?)",
                (str(p), int(level), labels_json, max_score),
            )
            print(f"  {level.name:12} | {p.name}")
        except Exception as e:
            print(f"  [err] {p.name}: {e}", file=sys.stderr)
    conn.commit()
    conn.close()
    print(f"[done] db: {db_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="单张图或目录")
    parser.add_argument("--db", default="media.db", help="SQLite 路径")
    parser.add_argument("--censor-out", help="若是硬核内容，打码到该路径")
    args = parser.parse_args()

    p = Path(args.path)
    if p.is_dir():
        index_directory(str(p), args.db)
    else:
        level, raw = classify(str(p))
        print(f"level: {level.name}")
        for r in raw:
            print(f"  {r['class']:32} score={r['score']:.3f} bbox={r.get('box')}")
        if args.censor_out:
            censored = censor_if_hardcore(str(p), args.censor_out)
            print(f"censored: {censored} -> {args.censor_out if censored else 'n/a'}")


if __name__ == "__main__":
    main()
