# LabscriptAI 后端 Docker 部署指南

本文档提供了 LabscriptAI 后端服务的完整 Docker 部署方案，使用 Docker Compose 进行容器化部署。

## 📋 目录结构

```
docker/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置文件
├── .dockerignore           # Docker构建忽略文件
├── .env.example            # 环境变量配置模板
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 配置环境变量

```bash
# 进入docker目录
cd docker

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env
```

**必须配置的环境变量：**
- `OPENAI_API_KEY`: OpenAI API 密钥
- `SECRET_KEY`: 应用安全密钥
- `CORS_ORIGINS`: 允许的跨域来源

### 3. 构建和启动服务

```bash
# 构建并启动服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看服务日志
docker compose logs -f backend
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

## ⚙️ 配置说明

### Docker Compose 服务配置

- **端口映射**: `8000:8000` (主机:容器)
- **资源限制**: CPU 2核，内存 2GB
- **健康检查**: 30秒间隔检查服务状态
- **重启策略**: `unless-stopped`

### 卷挂载

- `./logs:/app/logs` - 日志文件持久化
- `./config:/app/config` - 配置文件挂载

### 网络配置

使用自定义桥接网络 `labscriptai-network`，便于服务间通信。

## 🔧 管理命令

### 服务管理

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f backend
```

### 镜像管理

```bash
# 重新构建镜像
docker compose build --no-cache

# 拉取最新镜像
docker compose pull

# 清理未使用的镜像
docker image prune -f
```

### 数据管理

```bash
# 备份日志数据
docker cp labscriptai-backend:/app/logs ./backup/logs

# 进入容器调试
docker compose exec backend bash

# 查看容器资源使用
docker stats labscriptai-backend
```

## 🔍 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 查看详细错误日志
docker compose logs backend

# 检查环境变量配置
docker compose config
```

#### 2. 端口冲突

```bash
# 检查端口占用
lsof -i :8000

# 修改docker-compose.yml中的端口映射
ports:
  - "8001:8000"  # 改为其他端口
```

#### 3. 内存不足

```bash
# 调整资源限制
deploy:
  resources:
    limits:
      memory: 1G  # 减少内存限制
```

#### 4. 健康检查失败

```bash
# 手动测试健康检查
curl -f http://localhost:8000/health

# 调整健康检查参数
healthcheck:
  interval: 60s     # 增加检查间隔
  timeout: 30s      # 增加超时时间
  start_period: 60s # 增加启动等待时间
```

### 性能优化

#### 1. 调整工作进程数

在 `.env` 文件中设置：
```bash
WORKERS=4  # 根据CPU核心数调整
```

#### 2. 启用缓存

```bash
# 添加Redis缓存服务
redis:
  image: redis:7-alpine
  container_name: labscriptai-redis
  ports:
    - "6379:6379"
  networks:
    - labscriptai-network
```

## 🔒 安全建议

1. **环境变量安全**
   - 不要将 `.env` 文件提交到版本控制
   - 使用强密码和随机密钥
   - 定期轮换API密钥

2. **网络安全**
   - 使用防火墙限制访问
   - 配置HTTPS证书
   - 限制CORS来源

3. **容器安全**
   - 定期更新基础镜像
   - 使用非root用户运行
   - 扫描镜像漏洞

## 📊 监控和日志

### 日志管理

```bash
# 查看最近100行日志
docker compose logs --tail=100 backend

# 按时间过滤日志
docker compose logs --since="2024-01-01T00:00:00" backend

# 导出日志到文件
docker compose logs backend > backend.log
```

### 性能监控

```bash
# 查看容器资源使用
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 查看容器进程
docker compose top backend
```

## 🚀 生产环境部署

### 1. 环境配置

```bash
# 生产环境变量
ENVIRONMENT=production
LOG_LEVEL=WARNING
WORKERS=4
```

### 2. 反向代理配置

建议使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 自动重启

```bash
# 设置开机自启
sudo systemctl enable docker

# 添加到crontab检查服务状态
*/5 * * * * cd /path/to/docker && docker compose ps | grep -q "Up" || docker compose up -d
```

## 📞 支持

如果您在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查 GitHub Issues
3. 联系技术支持团队

---

**注意**: 请确保在生产环境中使用强密码和安全配置。