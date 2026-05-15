# 使用 nginx:alpine 作为基础镜像
FROM nginx:alpine

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
