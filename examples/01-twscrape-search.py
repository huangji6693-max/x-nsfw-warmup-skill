"""
Example 01 · twscrape Search
============================

用 twscrape 找成人内容方向的 tweet + creator。

依赖：
    pip install twscrape

文档：https://github.com/vladkens/twscrape
"""

import asyncio
import json
from pathlib import Path

from twscrape import API, gather


SCRAPER_ACCOUNTS = [
    # 一次性号，专门给 scraping 用，不要混入养号池
    # ("username", "password", "email", "email_password"),
]


async def setup_pool(api: API):
    """加载 scraping 用账号池（首次跑时）"""
    for u, p, e, ep in SCRAPER_ACCOUNTS:
        await api.pool.add_account(u, p, e, ep)
    if SCRAPER_ACCOUNTS:
        await api.pool.login_all()


async def search_keyword(api: API, query: str, limit: int = 200):
    """关键词 / hashtag 搜索（仅带媒体，过滤转推）"""
    results = []
    async for tweet in api.search(f"{query} filter:media -filter:retweets", limit=limit):
        photos = []
        if tweet.media and tweet.media.photos:
            photos = [p.url for p in tweet.media.photos]
        videos = []
        if tweet.media and tweet.media.videos:
            videos = [v.variants[-1].url for v in tweet.media.videos if v.variants]
        if not (photos or videos):
            continue
        results.append({
            "id": tweet.id,
            "user": tweet.user.username,
            "user_followers": tweet.user.followersCount,
            "text": tweet.rawContent,
            "photos": photos,
            "videos": videos,
            "likes": tweet.likeCount,
            "retweets": tweet.retweetCount,
            "url": tweet.url,
        })
    return results


async def list_creators_from_hashtag(api: API, hashtag: str, limit: int = 300):
    """从 hashtag 收割活跃 creator（粉丝 > 1000，发推 > 100）"""
    creators = {}
    async for tweet in api.search(f"#{hashtag}", limit=limit):
        u = tweet.user
        if u.followersCount < 1000 or u.statusesCount < 100:
            continue
        if u.username in creators:
            continue
        creators[u.username] = {
            "handle": u.username,
            "name": u.displayname,
            "followers": u.followersCount,
            "following": u.friendsCount,
            "tweets": u.statusesCount,
            "verified": u.verified,
            "bio": u.rawDescription,
            "discovered_via": hashtag,
        }
    return list(creators.values())


async def fetch_user_timeline(api: API, handle: str, limit: int = 50):
    """拉单个 creator 的最新推文"""
    user = await api.user_by_login(handle)
    if not user:
        return []
    return await gather(api.user_tweets(user.id, limit=limit))


async def main():
    api = API()
    await setup_pool(api)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    # 1. 关键词搜索
    keywords = ["#nsfw lang:en", "#lewd lang:en", "#adult lang:en"]
    all_tweets = []
    for kw in keywords:
        print(f"[*] searching: {kw}")
        tweets = await search_keyword(api, kw, limit=100)
        all_tweets.extend(tweets)
        print(f"    + {len(tweets)} tweets")
    (out_dir / "tweets.json").write_text(json.dumps(all_tweets, indent=2))

    # 2. 收割 creator
    hashtags = ["nsfw", "lewd"]
    all_creators = {}
    for h in hashtags:
        print(f"[*] mining creators from #{h}")
        creators = await list_creators_from_hashtag(api, h, limit=200)
        for c in creators:
            all_creators[c["handle"]] = c
        print(f"    + {len(creators)} creators (total {len(all_creators)})")
    (out_dir / "creators.json").write_text(json.dumps(list(all_creators.values()), indent=2))

    print(f"\n[done] tweets={len(all_tweets)} creators={len(all_creators)}")
    print(f"[done] output dir: {out_dir.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
