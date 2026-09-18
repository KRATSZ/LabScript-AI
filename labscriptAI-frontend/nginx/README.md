# 前端部署指南

LabscriptAI 前端是 React + Vite 构建的 SPA 应用。本目录包含不同部署场景的 Nginx 配置文件。

## 📁 配置文件对照

| 配置文件 | 适用场景 | 说明 |
|---------|---------|------|
| `openresty-labscriptai.conf` | **生产部署**（推荐） | OpenResty + 1Panel，同域部署前端 + API 反代 |
| `nginx-docker.conf` | Docker 容器部署 | Docker 环境下的完整配置（含 API 代理） |
| `nginx.conf` | 旧版配置 | 参考，路径已过时，不建议使用 |

---

## 🚀 方案一：OpenResty + 1Panel（推荐）

这是你的生产环境实际使用的方案。

### 1. 本地构建前端

```bash
cd labscriptAI-frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，`dist/` 目录包含所有静态文件（约 22MB）。

### 2. 上传到服务器

```bash
# 上传 dist/ 目录内容到服务器
scp -r dist/* user@your-server:/opt/1panel/www/sites/labscriptai.cn/index/dist/
```

### 3. 配置 `VITE_API_BASE_URL`

前端开发环境默认 API 地址是 `http://127.0.0.1:8000`。生产构建用于同域部署时，应该将 `VITE_API_BASE_URL` 留空，让浏览器请求当前域名下的 `/api/`，再由 Nginx 反代到后端。

**构建前**确认 `labscriptAI-frontend/.env`（或 `.env.local`）：

```bash
# 留空表示使用同域请求，通过 /api/ 转发
VITE_API_BASE_URL=
```

生产构建会自动忽略 `localhost` / `127.0.0.1` 这类开发地址，避免把本机 API 地址打进线上包。修改环境变量后必须重新执行 `npm run build` 并重新上传 `dist/`。

### 4. 应用 OpenResty 配置

1. 登录 1Panel 面板
2. 进入「网站」→ 选择 `labscriptai.cn`
3. 点击「配置文件」，将 `openresty-labscriptai.conf` 的内容粘贴进去
4. 关键配置项检查：

```nginx
server_name labscriptai.cn;

# 静态文件运行目录
root /opt/1panel/www/sites/labscriptai.cn/index/dist;

# API 反代地址（容器内 8000，映射到主机 9002）
location /api/ {
    proxy_pass http://127.0.0.1:9002;
}
```

5. 点击「保存并重载」

### 5. 验证

```bash
# 访问前端
curl https://labscriptai.cn

# 测试 API 反代
curl https://labscriptai.cn/api/health

# 预期返回：{"status":"healthy"}
```

---

## 🐳 方案二：Docker 部署

如果前后端都用 Docker，使用 `docker-compose.yml`：

```bash
cd labscriptAI-frontend/nginx

# 启动前端 + 后端
docker compose up -d

# 访问前端
open http://localhost
```

此方案会自动拉取 Dockerfile 构建前端，并启动后端服务。

---

## 🔧 常见问题

### API 请求失败（CORS 401/403）

**原因**：前端直接请求后端地址，跨域被拦截

**解决**：
1. 确保 `VITE_API_BASE_URL` 为空（同域模式）
2. 检查后端 `CORS_ORIGINS` 是否包含你的域名

### 502 Bad Gateway

**原因**：后端服务未启动或端口错误

**解决**：
```bash
# 检查后端服务
docker compose ps backend  # 或 systemctl status otcode-api

# 检查端口监听
lsof -i :9002
```

### 静态资源缓存不更新

**原因**：浏览器缓存了旧的 `.js` 文件

**解决**：
1. 构建后文件名带 hash（Vite 默认行为），强制清除缓存
2. 手动刷新（Ctrl+Shift+R）
3. 检查 Nginx 配置中 `Cache-Control: no-cache` 是否对 HTML 生效

### 路由刷新 404

**原因**：SPA 路由需要 Nginx fallback 到 `index.html`

**解决**：确认配置中有：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 📋 后端健康检查

后端健康检查端点：`/api/health`

```bash
# 容器内测试
curl http://localhost:8000/api/health

# 从主机测试（通过端口映射）
curl http://localhost:9002/api/health
```

---

## 🌐 多环境切换

| 环境 | VITE_API_BASE_URL | Nginx proxy_pass |
|------|------------------|-----------------|
| 本地开发 | 未设置或 `http://127.0.0.1:8000` | 无需配置 |
| 1Panel 生产 | 空 | `http://127.0.0.1:9002` |
| Docker 生产 | 空 | `http://backend:8000` |
