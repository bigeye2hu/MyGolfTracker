# Windows PowerShell停止脚本
Write-Host "🛑 停止GolfTracker GPU服务..." -ForegroundColor Yellow

docker-compose -f docker-compose.gpu.yml down

Write-Host "✅ 服务已停止" -ForegroundColor Green

