#!/usr/bin/env python3
"""
测试应用导入
"""

try:
    from app.main import app
    print("✅ 应用导入成功")
    
    # 检查路由
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    
    print(f"📋 可用路由: {len(routes)} 个")
    for route in routes[:10]:  # 显示前10个路由
        print(f"  - {route}")
    
    # 检查模型管理路由
    model_routes = [r for r in routes if '/models' in r]
    print(f"🤖 模型管理路由: {len(model_routes)} 个")
    for route in model_routes:
        print(f"  - {route}")
        
except Exception as e:
    print(f"❌ 应用导入失败: {e}")
    import traceback
    traceback.print_exc()
