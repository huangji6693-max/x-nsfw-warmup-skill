#!/usr/bin/env bash
# Example 04 · gallery-dl Batch
# =============================
#
# 用 gallery-dl 批量下载 Twitter / Coomer / Kemono / Reddit 的素材。
#
# 依赖：
#     pip install gallery-dl
#
# 文档：https://github.com/mikf/gallery-dl

set -euo pipefail

OUT_DIR="${OUT_DIR:-./downloads}"
CONFIG_FILE="${CONFIG_FILE:-$HOME/.config/gallery-dl/config.json}"

mkdir -p "$OUT_DIR"

# ----------------------------------------------------------------------------
# 1. 准备 config（首次运行）
# ----------------------------------------------------------------------------
if [ ! -f "$CONFIG_FILE" ]; then
  mkdir -p "$(dirname "$CONFIG_FILE")"
  cat > "$CONFIG_FILE" <<'JSON'
{
  "extractor": {
    "base-directory": "./downloads/",
    "twitter": {
      "videos": true,
      "include": "media",
      "filename": "{user[name]}_{tweet_id}_{num}.{extension}",
      "directory": ["twitter", "{user[name]}"],
      "retweets": false,
      "quoted": false,
      "replies": false,
      "cookies": null,
      "sleep-request": [2, 5]
    },
    "coomer": {
      "filename": "{username}_{id}_{filename}.{extension}",
      "directory": ["coomer", "{service}", "{username}"],
      "sleep-request": [3, 7]
    },
    "kemono": {
      "filename": "{username}_{id}_{filename}.{extension}",
      "directory": ["kemono", "{service}", "{username}"],
      "sleep-request": [3, 7]
    },
    "reddit": {
      "client-id": null,
      "user-agent": "gallery-dl bot/1.0",
      "directory": ["reddit", "{subreddit}"],
      "filename": "{id}_{title[:60]}.{extension}",
      "sleep-request": [2, 5]
    }
  },
  "output": {
    "mode": "auto",
    "progress": true,
    "log": "[{name}][{levelname}] {message}"
  }
}
JSON
  echo "[+] config created at $CONFIG_FILE"
fi

# ----------------------------------------------------------------------------
# 2. 批量下载 Twitter 用户媒体
# ----------------------------------------------------------------------------
TWITTER_USERS_FILE="${TWITTER_USERS_FILE:-twitter_users.txt}"
if [ -f "$TWITTER_USERS_FILE" ]; then
  echo "[*] downloading from Twitter users in $TWITTER_USERS_FILE"
  while IFS= read -r user || [ -n "$user" ]; do
    [ -z "$user" ] && continue
    [[ "$user" =~ ^# ]] && continue
    user="${user#@}"
    echo "  ▶ @$user"
    gallery-dl "https://x.com/${user}/media" || true
  done < "$TWITTER_USERS_FILE"
fi

# ----------------------------------------------------------------------------
# 3. 批量下载 Coomer creator
# ----------------------------------------------------------------------------
COOMER_LIST="${COOMER_LIST:-coomer_creators.txt}"
if [ -f "$COOMER_LIST" ]; then
  echo "[*] downloading from Coomer creators in $COOMER_LIST"
  while IFS=":" read -r service username || [ -n "$service" ]; do
    [ -z "$service" ] && continue
    [[ "$service" =~ ^# ]] && continue
    echo "  ▶ $service/$username"
    gallery-dl "https://coomer.su/${service}/user/${username}" || true
  done < "$COOMER_LIST"
fi

# ----------------------------------------------------------------------------
# 4. 批量下载 Kemono creator
# ----------------------------------------------------------------------------
KEMONO_LIST="${KEMONO_LIST:-kemono_creators.txt}"
if [ -f "$KEMONO_LIST" ]; then
  echo "[*] downloading from Kemono creators in $KEMONO_LIST"
  while IFS=":" read -r service userid || [ -n "$service" ]; do
    [ -z "$service" ] && continue
    [[ "$service" =~ ^# ]] && continue
    echo "  ▶ $service/$userid"
    gallery-dl "https://kemono.su/${service}/user/${userid}" || true
  done < "$KEMONO_LIST"
fi

# ----------------------------------------------------------------------------
# 5. Reddit subreddit
# ----------------------------------------------------------------------------
REDDIT_LIST="${REDDIT_LIST:-reddit_subs.txt}"
if [ -f "$REDDIT_LIST" ]; then
  echo "[*] downloading from subreddits in $REDDIT_LIST"
  while IFS= read -r sub || [ -n "$sub" ]; do
    [ -z "$sub" ] && continue
    [[ "$sub" =~ ^# ]] && continue
    sub="${sub#r/}"
    echo "  ▶ r/$sub"
    gallery-dl "https://www.reddit.com/r/${sub}/" || true
  done < "$REDDIT_LIST"
fi

echo ""
echo "[done] check $OUT_DIR"
