# 策略管理库使用指南

## 概述

策略管理库是一个灵活的轨迹优化策略管理系统，允许你自定义和命名不同的优化算法，并轻松在双画面播放器中进行对比。

## 核心组件

### 1. 策略管理器 (`analyzer/strategy_manager.py`)
- **StrategyManager**: 管理所有策略的注册、获取和应用
- **OptimizationStrategy**: 策略基类，所有策略都需要继承此类
- **StrategyInfo**: 策略信息数据类，包含ID、名称、描述等

### 2. 自定义策略 (`analyzer/custom_strategies.py`)
- **CustomSmoothingStrategy**: 高尔夫挥杆专用平滑策略
- **FastMotionStrategy**: 快速移动优化策略
- **ConservativeStrategy**: 保守优化策略

### 3. 轨迹优化器 (`analyzer/trajectory_optimizer.py`)
- 集成了策略管理库
- 支持使用指定策略进行优化
- 提供策略查询接口

## 内置策略

### 默认策略
1. **Savitzky-Golay滤波** (`savitzky_golay`)
   - 类别: smoothing
   - 描述: 使用Savitzky-Golay滤波器平滑轨迹，保持峰值特征
   - 参数: window_length=5, polyorder=2

2. **卡尔曼滤波** (`kalman_filter`)
   - 类别: prediction
   - 描述: 使用卡尔曼滤波器进行轨迹预测和平滑
   - 参数: process_noise=0.1, measurement_noise=0.5

3. **线性插值** (`linear_interpolation`)
   - 类别: interpolation
   - 描述: 对缺失点进行线性插值填充
   - 参数: max_gap=5

4. **异常值移除** (`outlier_removal`)
   - 类别: cleaning
   - 描述: 移除轨迹中的异常跳跃点
   - 参数: threshold=0.1, min_points=3

### 自定义策略
1. **高尔夫挥杆平滑** (`custom_smoothing`)
   - 类别: golf_specific
   - 描述: 专门为高尔夫挥杆轨迹设计的平滑算法
   - 参数: smooth_factor=0.3, velocity_threshold=0.05

2. **快速移动优化** (`fast_motion`)
   - 类别: motion
   - 描述: 专门处理快速移动物体的轨迹优化
   - 参数: prediction_frames=2, smoothing_window=3

3. **保守优化** (`conservative`)
   - 类别: conservative
   - 描述: 最小化修改原始检测数据
   - 参数: max_adjustment=0.02, confidence_threshold=0.8

## 如何添加自定义策略

### 1. 创建策略类

```python
from analyzer.strategy_manager import OptimizationStrategy, StrategyInfo

class MyCustomStrategy(OptimizationStrategy):
    def __init__(self):
        super().__init__(StrategyInfo(
            id="my_custom_strategy",
            name="我的自定义策略",
            description="这是我自定义的轨迹优化策略",
            category="custom",
            parameters={
                "param1": 0.5,
                "param2": 10
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        # 实现你的优化逻辑
        param1 = kwargs.get('param1', self.info.parameters['param1'])
        param2 = kwargs.get('param2', self.info.parameters['param2'])
        
        # 优化算法实现
        result = []
        for point in trajectory:
            # 你的优化逻辑
            optimized_point = self._my_optimization(point, param1, param2)
            result.append(optimized_point)
        
        return result
    
    def _my_optimization(self, point, param1, param2):
        # 具体的优化算法
        return point
```

### 2. 注册策略

在 `analyzer/custom_strategies.py` 中添加：

```python
def register_custom_strategies(strategy_manager):
    custom_strategies = [
        # ... 现有策略
        MyCustomStrategy()
    ]
    
    for strategy in custom_strategies:
        strategy_manager.register_strategy(strategy)
```

### 3. 使用策略

```python
# 在轨迹优化器中使用
optimizer = TrajectoryOptimizer()
optimized_trajectory, scores = optimizer.optimize_with_strategy(
    trajectory, 
    "my_custom_strategy",
    param1=0.8,  # 自定义参数
    param2=15
)
```

## API 接口

### 获取所有策略
```
GET /analyze/strategies
```

### 按类别获取策略
```
GET /analyze/strategies/{category}
```

### 前端使用

双画面播放器会自动从后端获取策略信息，并在下拉菜单中显示：

```javascript
// 策略选择器会自动更新
const select = document.getElementById('dualOptimizationSelect');
// 选项包括：
// - 原始检测
// - 标准优化  
// - 快速移动优化
// - 你的自定义策略...
```

## 策略参数调优

每个策略都支持参数调优，可以通过以下方式调整：

1. **修改默认参数**：在策略类的 `__init__` 方法中修改 `parameters`
2. **运行时调整**：在调用 `optimize_with_strategy` 时传入参数
3. **前端界面**：可以在前端添加参数调整界面

## 策略分类

- **smoothing**: 平滑类策略
- **prediction**: 预测类策略  
- **interpolation**: 插值类策略
- **cleaning**: 清理类策略
- **golf_specific**: 高尔夫专用策略
- **motion**: 运动优化策略
- **conservative**: 保守策略
- **custom**: 自定义策略

## 最佳实践

1. **命名规范**：使用描述性的策略名称和ID
2. **参数设计**：提供合理的默认参数值
3. **错误处理**：在策略中处理异常情况
4. **性能考虑**：避免过于复杂的算法影响实时性
5. **文档说明**：为每个策略提供清晰的描述

## 调试和测试

1. **日志输出**：策略注册时会输出日志
2. **参数验证**：检查参数的有效性
3. **回退机制**：策略失败时回退到默认优化
4. **性能监控**：监控策略执行时间

通过这个策略管理库，你可以轻松地添加、管理和对比不同的轨迹优化算法，找到最适合你需求的优化策略！
