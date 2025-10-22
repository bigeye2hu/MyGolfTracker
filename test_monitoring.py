#!/usr/bin/env python3
"""
测试监控功能的脚本
"""
import requests
import time
import json

def test_monitoring_endpoints():
    """测试监控端点"""
    base_url = "http://localhost:5005"
    
    print("🔍 测试监控端点...")
    
    # 测试监控仪表板
    try:
        response = requests.get(f"{base_url}/monitoring/dashboard", timeout=10)
        if response.status_code == 200:
            print("✅ 监控仪表板可访问")
        else:
            print(f"❌ 监控仪表板返回状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 监控仪表板访问失败: {e}")
    
    # 测试监控API
    try:
        response = requests.get(f"{base_url}/monitoring/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 监控API响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 监控API返回状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 监控API访问失败: {e}")
    
    # 生成一些测试请求来产生数据
    print("\n📊 生成测试请求数据...")
    endpoints = ["/healthz", "/health", "/metrics"]
    
    for i in range(5):
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                print(f"  {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"  {endpoint}: 错误 - {e}")
        time.sleep(1)
    
    print("\n✅ 测试完成！现在可以访问监控仪表板查看数据")

if __name__ == "__main__":
    test_monitoring_endpoints()
