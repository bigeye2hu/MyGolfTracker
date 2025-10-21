# Windows PowerShell启动脚本
Write-Host "🚀 启动GolfTracker GPU服务..." -ForegroundColor Green

# 检查Docker是否运行
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 检查GPU
Write-Host "🎮 检查GPU状态..." -ForegroundColor Cyan
nvidia-smi

# 启动服务
Write-Host "🔨 构建并启动服务..." -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml up -d --build

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml ps

# 显示日志
Write-Host "📝 最新日志：" -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml logs --tail=20

Write-Host "`n✅ 服务已启动！" -ForegroundColor Green
Write-Host "🌐 访问地址: http://localhost:5005/analyze/server-test" -ForegroundColor Green
Write-Host "🔍 健康检查: http://localhost:5005/health" -ForegroundColor Green

# 自动打开浏览器
Start-Process "http://localhost:5005/analyze/server-test"

