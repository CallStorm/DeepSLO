# Docker 部署指南

本项目提供了 Dockerfile，支持一键构建和运行 DeepSLO 应用。

## 构建镜像

```bash
docker build -t deepslo:latest .
```

## 运行容器

### 基本运行

```bash
docker run -d \
  --name deepslo \
  -p 8000:8000 \
  -e MYSQL_HOST=your_mysql_host \
  -e MYSQL_USER=your_mysql_user \
  -e MYSQL_PASSWORD=your_mysql_password \
  -e MYSQL_DB=deepslo \
  deepslo:latest
```

### 使用默认配置（需要外部 MySQL）

```bash
docker run -d \
  --name deepslo \
  -p 8000:8000 \
  deepslo:latest
```

默认 MySQL 配置：
- Host: `10.72.2.49`
- User: `deepslo`
- Password: `deepslo`
- Database: `deepslo`
- Port: `3306`

### 使用 Docker Compose（推荐）

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  deepslo:
    build: .
    ports:
      - "8000:8000"
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: deepslo
      MYSQL_PASSWORD: deepslo
      MYSQL_DB: deepslo
      MYSQL_PORT: 3306
    depends_on:
      - mysql
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: deepslo
      MYSQL_USER: deepslo
      MYSQL_PASSWORD: deepslo
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    restart: unless-stopped

volumes:
  mysql_data:
```

然后运行：

```bash
docker-compose up -d
```

## 访问应用

构建完成后，访问：
- 前端界面：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

默认登录账号：`admin / admin`（请立即修改密码）

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MYSQL_HOST | 10.72.2.49 | MySQL 主机地址 |
| MYSQL_USER | deepslo | MySQL 用户名 |
| MYSQL_PASSWORD | deepslo | MySQL 密码 |
| MYSQL_PORT | 3306 | MySQL 端口 |
| MYSQL_DB | deepslo | MySQL 数据库名 |

## 注意事项

1. **数据库准备**：确保 MySQL 数据库已创建，或者使用 Docker Compose 自动创建
2. **网络连接**：如果 MySQL 在容器外部，确保容器能够访问 MySQL 主机
3. **数据持久化**：建议使用 Docker volumes 持久化数据库数据
4. **生产环境**：生产环境建议使用反向代理（如 Nginx）和 HTTPS

## 故障排查

### 检查容器日志

```bash
docker logs deepslo
```

### 进入容器调试

```bash
docker exec -it deepslo /bin/bash
```

### 检查数据库连接

```bash
docker exec -it deepslo python -c "from backend.db import engine; print(engine.url)"
```

