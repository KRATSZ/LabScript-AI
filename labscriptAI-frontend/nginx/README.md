# Nginx 部署配置说明

本文件夹包含了 LabscriptAI 前端应用的 Nginx 配置文件，用于生产环境部署。

## 📁 文件说明

- `nginx.conf` - 主要的 Nginx 配置文件
- `README.md` - 本说明文件

## 🚀 部署步骤

### 1. 构建前端应用

```bash
# 在 labscriptAI-frontend 目录下执行
npm run build
```

构建完成后，会在 `dist/` 目录下生成静态文件。

### 2. 部署到服务器

将 `dist/` 目录下的所有文件上传到服务器的 `/var/www/labscriptai/dist/` 目录。

```bash
# 创建部署目录
sudo mkdir -p /var/www/labscriptai

# 复制构建文件
sudo cp -r dist/* /var/www/labscriptai/dist/

# 设置权限
sudo chown -R nginx:nginx /var/www/labscriptai
sudo chmod -R 755 /var/www/labscriptai
```

### 3. 配置 Nginx

```bash
# 复制配置文件到 Nginx 配置目录
sudo cp nginx/nginx.conf /etc/nginx/sites-available/labscriptai

# 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/labscriptai /etc/nginx/sites-enabled/

# 测试配置文件语法
sudo nginx -t

# 重新加载 Nginx 配置
sudo systemctl reload nginx
```

### 4. 启动服务

```bash
# 启动 Nginx
sudo systemctl start nginx

# 设置开机自启
sudo systemctl enable nginx

# 检查状态
sudo systemctl status nginx
```

## ⚙️ 配置说明

### 静态文件服务
- 网站根目录：`/var/www/labscriptai/dist`
- 支持 gzip 压缩，减少传输大小
- 静态资源缓存 1 年，HTML 文件不缓存

### API 代理
- 所有 `/api/` 请求代理到后端服务器
- 默认代理到 `http://api.ai4ot.cn:8000`
- 可修改为本地后端：`http://127.0.0.1:8000`

### CORS 支持
- 允许跨域访问
- 支持所有常用 HTTP 方法
- 正确处理预检请求

### SPA 路由
- 所有未匹配的路由都返回 `index.html`
- 支持 React Router 等前端路由

### 安全配置
- 添加了安全头部
- 禁止访问隐藏文件和备份文件
- 配置了错误页面

## 🔧 自定义配置

### 修改域名

在 `nginx.conf` 中修改 `server_name`：

```nginx
server_name your-domain.com www.your-domain.com;
```

### 修改后端 API 地址

在 `location /api/` 块中修改 `proxy_pass`：

```nginx
proxy_pass http://your-backend-server:8000;
```

### 启用 HTTPS

取消注释配置文件中的 HTTPS 部分，并配置 SSL 证书路径。

## 📝 日志文件

- 访问日志：`/var/log/nginx/labscriptai_access.log`
- 错误日志：`/var/log/nginx/labscriptai_error.log`

## 🔍 故障排除

### 检查 Nginx 状态

```bash
sudo systemctl status nginx
```

### 查看错误日志

```bash
sudo tail -f /var/log/nginx/labscriptai_error.log
```

### 测试配置文件

```bash
sudo nginx -t
```

### 重新加载配置

```bash
sudo systemctl reload nginx
```

## 📋 注意事项

1. 确保服务器防火墙开放 80 和 443 端口
2. 如果使用 HTTPS，需要配置 SSL 证书
3. 定期检查日志文件，监控应用运行状态
4. 建议配置日志轮转，避免日志文件过大

## 🌐 域名配置

当前配置支持以下域名访问：
- `ai4ot.cn`
- `www.ai4ot.cn`

如需修改，请更新配置文件中的 `server_name` 指令。