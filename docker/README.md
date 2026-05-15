# Docker 部署目录

本目录包含 IELTS 词汇学习应用的所有 Docker 相关配置文件。

## 目录结构

```
docker/
├── frontend/                 # 前端配置
│   ├── Dockerfile            # 前端 Docker 镜像
│   └── nginx.conf           # Nginx 配置
├── backend/                  # 后端配置
│   ├── Dockerfile            # 后端 Docker 镜像
│   └── requirements.txt     # Python 依赖
├── postgres/                 # 数据库配置
│   └── 01-init.sql         # 数据库初始化脚本
├── nginx-proxy/             # 反向代理配置
│   └── nginx.conf           # Nginx 反向代理配置
├── docker-compose.yml       # 生产环境配置
├── docker-compose.dev.yml   # 开发环境配置
├── .env.example            # 环境变量示例
├── build.sh                # 构建脚本
├── start.sh                # 启动脚本
└── stop.sh                 # 停止脚本
```

## 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 根据实际情况修改 .env 文件
```

### 2. 构建镜像

```bash
# 生产环境
bash build.sh production

# 开发环境
bash build.sh development
```

### 3. 启动服务

```bash
# 生产环境
bash start.sh production

# 开发环境
bash start.sh development
```

### 4. 访问应用

#### 生产环境
- 前端: http://localhost:8080
- 后端 API: http://localhost:8000
- 后端文档: http://localhost:8000/docs
- 数据库: localhost:5432
- Redis: localhost:6379

#### 开发环境
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- 后端文档: http://localhost:8000/docs
- 数据库: localhost:5432
- Redis: localhost:6379

## 服务说明

### 前端服务 (frontend)
- **镜像**: 自定义构建（基于 Node.js + Nginx）
- **端口**: 8080 (生产) / 3000 (开发)
- **功能**: Vue.js 前端应用

### 后端服务 (backend)
- **镜像**: 自定义构建（基于 Python 3.10）
- **端口**: 8000
- **功能**: FastAPI 后端服务

### PostgreSQL 数据库
- **镜像**: postgres:15-alpine
- **端口**: 5432
- **用户**: ielts
- **密码**: ielts_password
- **数据库**: ielts_db
- **数据卷**: postgres-data

### Redis 缓存
- **镜像**: redis:7-alpine
- **端口**: 6379
- **数据卷**: redis-data

### Nginx 反向代理（生产环境）
- **镜像**: nginx:alpine
- **端口**: 80, 443
- **功能**: HTTPS 支持、负载均衡

## 常用命令

### 构建

```bash
# 生产环境
docker-compose -f docker-compose.yml build

# 开发环境
docker-compose -f docker-compose.dev.yml build

# 重新构建（不使用缓存）
docker-compose -f docker-compose.yml build --no-cache

# 单独构建某个服务
docker-compose -f docker-compose.yml build frontend
```

### 启动

```bash
# 生产环境
docker-compose -f docker-compose.yml up -d

# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.yml logs -f frontend
```

### 停止

```bash
# 停止服务
docker-compose -f docker-compose.yml down

# 停止并删除数据卷（谨慎使用）
docker-compose -f docker-compose.yml down -v

# 使用脚本停止
bash stop.sh production
```

### 管理容器

```bash
# 查看容器状态
docker-compose -f docker-compose.yml ps

# 重启服务
docker-compose -f docker-compose.yml restart

# 重启特定服务
docker-compose -f docker-compose.yml restart backend

# 进入容器
docker-compose -f docker-compose.yml exec frontend sh
docker-compose -f docker-compose.yml exec backend bash

# 查看资源使用
docker stats
```

## 数据卷

### 持久化数据

- `postgres-data`: PostgreSQL 数据库数据
- `redis-data`: Redis 缓存数据
- `./backend/logs`: 后端日志（开发环境）

### 备份数据

```bash
# 备份 PostgreSQL
docker exec ielts-postgres pg_dump -U ielts ielts_db > backup.sql

# 恢复 PostgreSQL
cat backup.sql | docker exec -i ielts-postgres psql -U ielts ielts_db

# 备份 Redis
docker exec ielts-redis redis-cli --rdb /data/backup.rdb
```

## 开发环境

### 热重载

开发环境已配置热重载功能：

- 前端：修改 `../src` 目录中的文件会自动重新加载
- 后端：修改 `../backend/app` 目录中的文件会自动重启

### 端口冲突

如果端口被占用，修改 `.env` 文件或 `docker-compose*.yml` 中的端口配置。

```yaml
ports:
  - "3001:80"  # 修改宿主机端口
```

## 生产环境

### HTTPS 配置

1. 准备 SSL 证书（cert.pem 和 key.pem）
2. 将证书放置在 `nginx-proxy/ssl/` 目录
3. 启动时包含 Nginx 反向代理：

```bash
docker-compose -f docker-compose.yml --profile production up -d
```

### 性能优化

1. 启用 Nginx 反向代理（生产环境）
2. 调整 worker 进程数
3. 配置缓存策略
4. 使用 CDN 加速静态资源

### 安全加固

1. 修改默认密码
2. 配置防火墙规则
3. 启用 HTTPS
4. 定期更新镜像
5. 配置日志轮转

## 监控和日志

### 查看日志

```bash
# 所有服务日志
docker-compose -f docker-compose.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.yml logs -f backend

# 最近 100 行日志
docker-compose -f docker-compose.yml logs --tail=100

# 查看容器标准输出
docker logs ielts-backend
```

### 健康检查

所有服务都配置了健康检查：

```bash
# 检查服务健康状态
docker-compose -f docker-compose.yml ps

# 查看健康检查详情
docker inspect ielts-backend | grep -A 10 Health
```

## 故障排除

### 容器无法启动

1. 查看日志：`docker-compose logs`
2. 检查端口是否被占用
3. 确认 Docker 守护进程运行正常
4. 检查磁盘空间

### 数据库连接失败

1. 确认 PostgreSQL 容器运行正常
2. 检查数据库连接字符串
3. 验证网络连接

### 前端无法访问后端

1. 检查 API_URL 配置
2. 确认网络配置正确
3. 查看浏览器控制台错误

## 更新和维护

### 更新镜像

```bash
# 重新构建镜像
docker-compose -f docker-compose.yml build --no-cache

# 重启服务
docker-compose -f docker-compose.yml up -d
```

### 清理资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的数据卷
docker volume prune

# 清理所有未使用的资源
docker system prune -a --volumes
```

## 生产环境部署清单

- [ ] 修改所有默认密码
- [ ] 配置 HTTPS 证书
- [ ] 配置环境变量
- [ ] 设置防火墙规则
- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 配置自动备份
- [ ] 压力测试
- [ ] 安全扫描

## 技术支持

如遇到问题，请检查：

1. Docker 版本（建议 20.10+）
2. Docker Compose 版本（建议 2.0+）
3. 系统资源（内存、磁盘）
4. 网络连接
5. 日志文件

## 许可证

本项目采用 MIT 许可证。
