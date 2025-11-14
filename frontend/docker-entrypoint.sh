#!/bin/sh
# Docker entrypoint脚本，用于在运行时替换环境变量

set -e

# 如果提供了VITE_API_BASE_URL环境变量，创建config.js文件
# 如果nginx代理了API（使用相对路径），则不需要config.js
if [ -n "$VITE_API_BASE_URL" ]; then
    # 创建config.js文件，包含运行时环境变量
    cat > /usr/share/nginx/html/config.js <<EOF
// 运行时环境配置
window.__ENV__ = {
  VITE_API_BASE_URL: "$VITE_API_BASE_URL"
};
EOF

    # 在index.html的head标签结束前注入config.js脚本
    # 确保在其他脚本之前加载，以便main.js可以使用
    if [ -f /usr/share/nginx/html/index.html ]; then
        if ! grep -q "config.js" /usr/share/nginx/html/index.html; then
            # 使用sed在</head>前插入config.js脚本
            # 注意：sed在不同系统上行为可能不同，这里使用更兼容的方式
            sed -i.bak 's|</head>|<script src="/config.js"></script></head>|' /usr/share/nginx/html/index.html
            rm -f /usr/share/nginx/html/index.html.bak 2>/dev/null || true
        fi
    fi
fi

# 执行nginx启动命令
exec "$@"

