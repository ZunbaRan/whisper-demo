# 启动开发环境
Write-Host "启动开发环境..." -ForegroundColor Green

# 1. 确保 Poetry 环境已安装
Write-Host "检查依赖..." -ForegroundColor Yellow
Set-Location whisper-core
poetry install
Set-Location ../gateway
poetry install
Set-Location ..

# 2. 启动 Docker 服务
Write-Host "启动 Docker 服务..." -ForegroundColor Yellow
docker-compose up --build 