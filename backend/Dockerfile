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

# 设置PYTHONPATH，使所有模块都能使用绝对导入
ENV PYTHONPATH=/app

# 启动命令
# main.py使用绝对导入，PYTHONPATH设置为/app后可以直接使用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

