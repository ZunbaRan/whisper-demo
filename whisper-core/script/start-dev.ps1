# 启动开发环境的 PowerShell 脚本

# 定义服务启动函数
function Start-Service {
    param (
        [string]$ServiceName,
        [string]$Directory,
        [int]$Port
    )
    Write-Host "正在启动 $ServiceName 服务..." -ForegroundColor Green
    Set-Location $Directory
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "poetry run uvicorn api.api:app --host 0.0.0.0 --port $Port --reload"
}

# 创建新的 PowerShell 窗口启动 whisper-core 服务
Start-Service -ServiceName "Whisper Core" -Directory "whisper-core" -Port 8001

# 创建新的 PowerShell 窗口启动 gateway 服务
Start-Service -ServiceName "Gateway" -Directory "gateway" -Port 8000

# 等待服务启动
Start-Sleep -Seconds 3

# 打开浏览器访问网关
Start-Process "http://localhost:8000"

Write-Host "`n服务已启动:" -ForegroundColor Green
Write-Host "Gateway: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Whisper Core: http://localhost:8001" -ForegroundColor Yellow
Write-Host "`n按 Ctrl+C 停止服务" -ForegroundColor Gray 