# 多阶段构建 Dockerfile for DeepSLO

# 第一阶段：构建前端
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm install

# 复制前端源代码
COPY frontend/ ./

# 构建前端生产版本
RUN npm run build

# 第二阶段：运行后端
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（MySQL客户端库等）
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件
COPY backend/requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 从第一阶段复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

# 暴露端口
EXPOSE 8000

# 设置环境变量（可通过docker run -e覆盖）
ENV MYSQL_USER=deepslo
ENV MYSQL_PASSWORD=deepslo
ENV MYSQL_HOST=10.72.2.49
ENV MYSQL_PORT=3306
ENV MYSQL_DB=deepslo

# 启动应用
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

