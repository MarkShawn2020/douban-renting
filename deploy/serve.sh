#!/bin/zsh
# 以 zsh 运行：~/.zshenv 提供 GAODE_WEB_SERVICE_API_KEY，密钥不进仓库和 plist
set -e
cd "${0:A:h}/.."
exec /Users/mark/.local/bin/uv run --frozen uvicorn web.app:app \
  --app-dir src --host 127.0.0.1 --port "${PORT:-8765}" --proxy-headers
