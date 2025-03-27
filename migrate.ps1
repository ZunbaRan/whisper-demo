# 设置错误时停止执行
$ErrorActionPreference = "Stop"

Write-Host "开始项目迁移..." -ForegroundColor Green

# 1. 创建新的目录结构
Write-Host "1. 创建目录结构..." -ForegroundColor Yellow
$directories = @(
    "whisper-core/api",
    "whisper-core/templates",
    "deep-research/api",
    "deep-research/templates",
    "web-crawl/src/crawler",
    "gateway"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "创建目录: $dir" -ForegroundColor Gray
    }
}

# 2. 移动文件
Write-Host "2. 移动文件..." -ForegroundColor Yellow

# 移动 api 文件夹内容到 whisper-core
if (Test-Path "api") {
    Write-Host "移动 api 文件到 whisper-core/api..." -ForegroundColor Gray
    Copy-Item "api\*" -Destination "whisper-core\api" -Recurse -Force
}

# 移动 templates 文件夹内容（如果存在）
if (Test-Path "templates") {
    Write-Host "移动 templates 文件到 whisper-core/templates..." -ForegroundColor Gray
    Copy-Item "templates\*" -Destination "whisper-core\templates" -Recurse -Force
}

# 3. 创建必要的空文件
Write-Host "3. 创建必要的文件..." -ForegroundColor Yellow
$files = @(
    "deep-research/api/__init__.py",
    "deep-research/api/api.py",
    "web-crawl/src/crawler/__init__.py",
    "web-crawl/src/crawler/api.py",
    "gateway/api.py"
)

foreach ($file in $files) {
    if (!(Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force
        Write-Host "创建文件: $file" -ForegroundColor Gray
    }
}

# 4. 创建 gateway/api.py 内容
$gatewayApiContent = @'
from fastapi import FastAPI
from httpx import AsyncClient
import uvicorn

app = FastAPI(title="API Gateway")

@app.get("/")
async def root():
    return {"message": "API Gateway is running"}

@app.get("/whisper/{path:path}")
async def whisper_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://whisper:8000/{path}")
        return response.json()

@app.get("/deep-research/{path:path}")
async def deep_research_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://deep-research:8000/{path}")
        return response.json()

@app.get("/web-crawl/{path:path}")
async def web_crawl_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://web-crawl:8000/{path}")
        return response.json()

def start_app():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_app()
'@

Set-Content -Path "gateway/api.py" -Value $gatewayApiContent

# 5. 初始化 Poetry 环境
Write-Host "5. 初始化 Poetry 环境..." -ForegroundColor Yellow

$projects = @("whisper-core", "deep-research", "web-crawl", "gateway")

foreach ($project in $projects) {
    Write-Host "正在设置 $project..." -ForegroundColor Gray
    Set-Location $project
    
    # 检查 pyproject.toml 是否已存在
    if (!(Test-Path "pyproject.toml")) {
        Write-Host "Error: $project/pyproject.toml 不存在！" -ForegroundColor Red
        Write-Host "请确保已经创建了 pyproject.toml 文件" -ForegroundColor Red
    }
    
    # 安装依赖
    try {
        poetry install
    }
    catch {
        Write-Host "Warning: $project poetry install 失败" -ForegroundColor Yellow
        Write-Host $_.Exception.Message
    }
    
    Set-Location ..
}

Write-Host "`n项目迁移完成！" -ForegroundColor Green
Write-Host "接下来的步骤：" -ForegroundColor Yellow
Write-Host "1. 检查各个服务的配置文件" -ForegroundColor Gray
Write-Host "2. 使用 'docker-compose up --build' 构建和启动服务" -ForegroundColor Gray
Write-Host "3. 访问 http://localhost:8000 测试网关服务" -ForegroundColor Gray 