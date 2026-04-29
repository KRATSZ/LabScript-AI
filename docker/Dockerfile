# 使用官方Python 3.11镜像作为基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install uv

# 设置工作目录
WORKDIR /app

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 使用uv安装主环境依赖
RUN uv sync --frozen --no-dev

# 创建Opentrons隔离环境(.ot_env)
# 这是项目双虚拟环境架构的关键部分，用于解决opentrons包的依赖冲突
RUN uv venv .ot_env --python 3.11 --seed

# 在.ot_env环境中安装opentrons包
RUN uv pip install --python .ot_env/bin/python opentrons==8.4.1

# 复制后端代码
COPY backend/ ./backend/
COPY main.py ./

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["uv", "run", "python", "main.py"]