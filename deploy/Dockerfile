# syntax=docker/dockerfile:1.6
#
# X NSFW Warmup Skill — production image
#
# Multi-stage build:
#   Stage 1 (builder): install deps + playwright browsers
#   Stage 2 (runtime): slim runtime with non-root user
#
# Build:
#   docker build -f deploy/Dockerfile -t x-warmup:latest .
#
# Run (dry-run smoke test):
#   docker run --rm x-warmup:latest python examples/05-full-warmup-loop.py --dry-run
#
# Run (live, requires .env + mounted volumes):
#   docker run -d --name x-warmup \
#     --env-file .env \
#     -v $(pwd)/data:/app/data \
#     -v $(pwd)/logs:/app/logs \
#     -v $(pwd)/screenshots:/app/screenshots \
#     x-warmup:latest

# ============================================================================
# Stage 1: builder
# ============================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 装 Python 依赖到一个独立 venv，方便第二阶段 COPY
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 预装 Playwright Chromium（放 builder 里，否则运行时下载慢）
RUN playwright install --with-deps chromium


# ============================================================================
# Stage 2: runtime
# ============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DEBIAN_FRONTEND=noninteractive

# Playwright Chromium 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libxshmfence1 \
    fonts-liberation fonts-noto-color-emoji fonts-noto-cjk \
    ca-certificates tini tzdata \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 拷贝 venv 和 Playwright browser 缓存
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /ms-playwright

# 非 root 用户
RUN groupadd -r warmup --gid 1000 && \
    useradd -r -g warmup --uid 1000 --home-dir /app --shell /bin/bash warmup && \
    mkdir -p /app/data /app/logs /app/screenshots && \
    chown -R warmup:warmup /app /ms-playwright

WORKDIR /app

# 拷贝应用代码（上下文是仓库根目录）
COPY --chown=warmup:warmup SKILL.md README.md LICENSE requirements.txt AI-AGENT-PLAYBOOK.md ./
COPY --chown=warmup:warmup examples/ ./examples/
COPY --chown=warmup:warmup workflows/ ./workflows/
COPY --chown=warmup:warmup tools-catalog.md ./
COPY --chown=warmup:warmup deploy/scripts/ ./scripts/

USER warmup

# 健康检查 —— 跑 dry-run 看能不能起来
HEALTHCHECK --interval=5m --timeout=60s --start-period=30s --retries=3 \
    CMD python examples/05-full-warmup-loop.py --dry-run > /dev/null 2>&1 || exit 1

# tini 做 PID 1，避免僵尸进程
ENTRYPOINT ["/usr/bin/tini", "--"]

# 默认命令 = dry-run（安全）；docker-compose 会覆盖为 live 启动器
CMD ["python", "examples/05-full-warmup-loop.py", "--dry-run"]
