# 后端Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
# 构建上下文是./backend，所以COPY . .会将backend目录的内容复制到/app
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
# main.py使用相对导入，需要作为Python模块运行
# 由于代码在/app目录下，直接使用main:app即可
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

