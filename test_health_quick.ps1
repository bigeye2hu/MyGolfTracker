# 快速测试健康检查端点的 PowerShell 脚本

Write-Host "🚀 测试 GolfTracker 服务健康检查端点" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 测试 /healthz 端点
Write-Host ""
Write-Host "🔍 测试 /healthz 端点:" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5005/healthz" -Method Get -TimeoutSec 10
    $response | ConvertTo-Json -Depth 3
    Write-Host "✅ /healthz 端点正常" -ForegroundColor Green
} catch {
    Write-Host "❌ /healthz 端点不可用: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试 /metrics 端点
Write-Host ""
Write-Host "🔍 测试 /metrics 端点:" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5005/metrics" -Method Get -TimeoutSec 10
    $content = $response.Content
    $lines = $content -split "`n" | Select-Object -First 20
    $lines | ForEach-Object { Write-Host $_ }
    Write-Host "✅ /metrics 端点正常" -ForegroundColor Green
} catch {
    Write-Host "❌ /metrics 端点不可用: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试原有 /health 端点
Write-Host ""
Write-Host "🔍 测试原有 /health 端点:" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5005/health" -Method Get -TimeoutSec 10
    $response | ConvertTo-Json -Depth 3
    Write-Host "✅ /health 端点正常" -ForegroundColor Green
} catch {
    Write-Host "❌ /health 端点不可用: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ 测试完成" -ForegroundColor Green
