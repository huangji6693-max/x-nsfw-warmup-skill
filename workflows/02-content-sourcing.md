# Workflow 02 · Content Sourcing

> 给养号循环喂内容。两个目标：找**待关注的成人 creator** + 找**可发布的素材**。

---

## 数据流

```
关键词 / hashtag / seed creator
        │
        ▼
┌────────────────────┐
│  twscrape          │ 找推文 + 找用户
│  snscrape          │
│  Scweet            │
└────────────────────┘
        │
        ▼ tweet_ids[], user_handles[]
┌────────────────────┐
│  gallery-dl        │ 拉媒体到本地
│  twmd / SCrawler   │
└────────────────────┘
        │
        ▼ images/*.jpg, videos/*.mp4
┌────────────────────┐
│  NudeNet           │ 自动打标签 + 评分
└────────────────────┘
        │
        ▼ classified_media.db
┌────────────────────┐
│  发布池 / 关注池    │
└────────────────────┘
```

---

## Step 1 · 用 twscrape 找候选推文

[twscrape](https://github.com/vladkens/twscrape) ⭐2330 是 2025 年最活跃的 X scraper。

### 安装

```bash
pip install twscrape
```

### 加号（用于授权 scraping，不会消耗你的养号池）

```python
import asyncio
from twscrape import API

async def main():
    api = API()
    # 用一些一次性账号专门做 scraping，不要混用养号池
    await api.pool.add_account("scraper_user1", "password1", "email1", "email_pass1")
    await api.pool.add_account("scraper_user2", "password2", "email2", "email_pass2")
    await api.pool.login_all()

asyncio.run(main())
```

### 关键词 / hashtag 搜索

```python
async def search_nsfw(api, keyword, limit=200):
    results = []
    async for tweet in api.search(f"{keyword} filter:media -filter:retweets", limit=limit):
        if tweet.media and len(tweet.media.photos) > 0:
            results.append({
                "id": tweet.id,
                "user": tweet.user.username,
                "text": tweet.rawContent,
                "media_urls": [p.url for p in tweet.media.photos],
                "likes": tweet.likeCount,
                "retweets": tweet.retweetCount,
            })
    return results

# 用法
tweets = await search_nsfw(api, "#nsfw lang:en", limit=500)
```

### 找 creator
```python
async def list_creators_who_engage(api, hashtag, limit=300):
    """从一个 hashtag 收割活跃 creator"""
    creators = {}
    async for tweet in api.search(f"#{hashtag}", limit=limit):
        u = tweet.user
        if u.followersCount > 1000 and u.statusesCount > 100:
            creators[u.username] = {
                "handle": u.username,
                "followers": u.followersCount,
                "tweets": u.statusesCount,
                "verified": u.verified,
                "bio": u.rawDescription,
            }
    return list(creators.values())
```

完整可运行版本见 [`examples/01-twscrape-search.py`](../examples/01-twscrape-search.py)。

---

## Step 2 · 拉媒体到本地

### gallery-dl（推荐）

```bash
pip install gallery-dl
```

支持的 URL 格式（直接喂就行）：

```bash
# 单条推文
gallery-dl "https://x.com/USERNAME/status/123456789"

# 整个用户的所有媒体
gallery-dl "https://x.com/USERNAME/media"

# Coomer / Kemono
gallery-dl "https://coomer.su/onlyfans/user/USERNAME"
gallery-dl "https://kemono.su/patreon/user/12345"

# Reddit subreddit
gallery-dl "https://www.reddit.com/r/SUBREDDIT/"
```

### 配置 cookie（避免触发限流）

`~/.config/gallery-dl/config.json`:

```json
{
  "extractor": {
    "twitter": {
      "cookies": "/path/to/twitter-cookies.txt",
      "videos": true,
      "include": "media",
      "filename": "{user[name]}_{tweet_id}_{num}.{extension}",
      "directory": ["twitter", "{user[name]}"]
    },
    "coomer": {
      "filename": "{username}_{id}_{filename}.{extension}",
      "directory": ["coomer", "{service}", "{username}"]
    }
  }
}
```

### twmd（轻量替代）

```bash
# 安装：https://github.com/mmpx12/twitter-media-downloader
twmd -u USERNAME -i -v -o /tmp/dl    # 下载用户所有图+视频
```

完整批量脚本见 [`examples/04-gallery-dl-batch.sh`](../examples/04-gallery-dl-batch.sh)。

---

## Step 3 · 候选 creator 入库

```sql
CREATE TABLE creators (
    handle TEXT PRIMARY KEY,
    followers INTEGER,
    tweets INTEGER,
    verified BOOLEAN,
    bio TEXT,
    discovered_via TEXT,        -- 哪个 hashtag 发现的
    nsfw_score REAL,             -- 后续 NudeNet 反向打分
    follow_priority INTEGER DEFAULT 5,  -- 1-10
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE media_items (
    id INTEGER PRIMARY KEY,
    source_tweet_id TEXT,
    source_creator TEXT,
    local_path TEXT,
    nsfw_labels TEXT,            -- JSON: ["FEMALE_BREAST_EXPOSED", ...]
    nsfw_max_score REAL,
    is_safe_to_post INTEGER DEFAULT 0,  -- 0 = 待审, 1 = 可发, -1 = 拒绝
    posted_count INTEGER DEFAULT 0
);
```

---

## Step 4 · 反向打分 creator（用 NudeNet）

```python
from nudenet import NudeDetector
detector = NudeDetector()

def score_creator(handle, sample_images):
    """对 creator 抽样的图片做 NSFW 打分，给 creator 整体打 0-1 分"""
    nsfw_count = 0
    for img in sample_images:
        results = detector.detect(img)
        if any(r["score"] > 0.5 for r in results if "EXPOSED" in r["class"]):
            nsfw_count += 1
    return nsfw_count / len(sample_images) if sample_images else 0

# 阈值过滤
creators_to_follow = [c for c in creators if score_creator(c["handle"], samples) > 0.3]
```

详见 [03-nsfw-classification.md](./03-nsfw-classification.md)。

---

## Step 5 · 输出给 L4 养号循环

养号循环的输入：

```python
{
    "creators_to_follow_random": ["@user1", "@user2", ...],   # 随机关
    "creators_to_follow_required": ["@vip_user1", ...],        # 必关
    "media_to_post": [
        {"path": "/data/img1.jpg", "caption": "Late night vibes 🌙"},
        ...
    ]
}
```

---

## ✅ 完成标志

- [ ] 至少 50 个 creator 已入库且打过分
- [ ] 至少 200 张图 / 50 个视频已下载且过 NudeNet
- [ ] 发布池有 7 天的内容缓冲量
- [ ] 关注池区分 random / required

完成后进入 [03-nsfw-classification.md](./03-nsfw-classification.md)。
