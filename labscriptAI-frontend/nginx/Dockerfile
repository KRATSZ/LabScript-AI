# Dockerfile for LabscriptAI Frontend
# 多阶段构建：先构建应用，再部署到nginx

# 第一阶段：构建应用
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 第二阶段：部署到nginx
FROM nginx:alpine

# 删除默认的nginx配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义nginx配置
COPY nginx/nginx-docker.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]