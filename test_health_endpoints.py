#!/usr/bin/env python3
"""
测试健康检查和监控端点的脚本
"""
import requests
import json
import time

def test_healthz():
    """测试 /healthz 端点"""
    print("🔍 测试 /healthz 端点...")
    try:
        response = requests.get("http://localhost:5005/healthz", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /healthz 响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 验证必要字段
            required_fields = ["status", "cuda", "model_loaded", "timestamp"]
            for field in required_fields:
                if field not in data:
                    print(f"❌ 缺少必要字段: {field}")
                    return False
            
            print("✅ /healthz 端点测试通过")
            return True
        else:
            print(f"❌ /healthz 端点返回错误状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ /healthz 端点请求失败: {e}")
        return False

def test_metrics():
    """测试 /metrics 端点"""
    print("\n🔍 测试 /metrics 端点...")
    try:
        response = requests.get("http://localhost:5005/metrics", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print("✅ /metrics 响应 (前500字符):")
            print(content[:500] + "..." if len(content) > 500 else content)
            
            # 检查是否包含 Prometheus 格式的指标
            if "http_requests_total" in content or "http_request_duration_seconds" in content:
                print("✅ /metrics 端点包含 Prometheus 指标")
                return True
            else:
                print("⚠️ /metrics 端点响应格式可能不正确")
                return False
        else:
            print(f"❌ /metrics 端点返回错误状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ /metrics 端点请求失败: {e}")
        return False

def test_original_health():
    """测试原有的 /health 端点"""
    print("\n🔍 测试原有 /health 端点...")
    try:
        response = requests.get("http://localhost:5005/health", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /health 响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ /health 端点返回错误状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ /health 端点请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 GolfTracker 服务端点...")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)
    
    results = []
    
    # 测试各个端点
    results.append(("healthz", test_healthz()))
    results.append(("metrics", test_metrics()))
    results.append(("health", test_original_health()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {endpoint}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个端点测试通过")
    
    if passed == total:
        print("🎉 所有端点测试通过！")
        return True
    else:
        print("⚠️ 部分端点测试失败，请检查服务状态")
        return False

if __name__ == "__main__":
    main()
