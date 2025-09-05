#!/usr/bin/env python3
"""
轨迹优化算法参数配置
"""

# 插值算法参数
INTERPOLATION_CONFIG = {
    "max_gap_size": 5,          # 最大连续缺失帧数
    "min_valid_points": 3,      # 最小有效点数
    "interpolation_method": "linear",  # 插值方法: linear, cubic, spline
    "extrapolation_enabled": True,     # 是否允许外推
    "max_extrapolation_frames": 3,     # 最大外推帧数
}

# 平滑算法参数
SMOOTHING_CONFIG = {
    "window_size": 5,           # 滤波窗口大小
    "poly_order": 2,            # 多项式阶数
    "smoothing_method": "savgol",  # 平滑方法: savgol, gaussian, moving_avg
    "sigma": 1.0,               # 高斯滤波标准差
}

# 物理约束参数
PHYSICS_CONFIG = {
    "max_velocity": 0.1,        # 最大速度阈值 (归一化坐标/帧)
    "max_acceleration": 0.05,   # 最大加速度阈值
    "min_velocity": 0.001,      # 最小速度阈值
    "gravity_effect": True,     # 是否考虑重力影响
    "gravity_constant": 0.001,  # 重力常数
}

# 异常值检测参数
OUTLIER_CONFIG = {
    "z_score_threshold": 2.5,   # Z-score阈值
    "iqr_multiplier": 1.5,      # IQR倍数
    "distance_threshold": 0.2,  # 距离阈值
    "velocity_threshold": 0.15, # 速度阈值
}

# 卡尔曼滤波参数
KALMAN_CONFIG = {
    "process_noise": 0.01,      # 过程噪声
    "measurement_noise": 0.1,   # 测量噪声
    "initial_covariance": 1.0,  # 初始协方差
    "state_dimension": 4,       # 状态维度 [x, y, vx, vy]
}

# 机器学习参数
ML_CONFIG = {
    "model_type": "lstm",       # 模型类型: lstm, transformer, cnn
    "sequence_length": 10,      # 输入序列长度
    "hidden_size": 64,          # 隐藏层大小
    "num_layers": 2,            # 层数
    "dropout": 0.2,             # Dropout率
    "learning_rate": 0.001,     # 学习率
    "batch_size": 32,           # 批次大小
    "epochs": 100,              # 训练轮数
}

# 性能参数
PERFORMANCE_CONFIG = {
    "max_processing_time": 0.1,  # 最大处理时间(秒)
    "memory_limit": 100,         # 内存限制(MB)
    "parallel_processing": True, # 是否并行处理
    "num_threads": 4,            # 线程数
}

# 可视化参数
VISUALIZATION_CONFIG = {
    "show_original": True,      # 显示原始轨迹
    "show_interpolated": True,  # 显示插值点
    "show_smoothed": True,      # 显示平滑轨迹
    "show_confidence": True,    # 显示置信度
    "point_size": 3,            # 点大小
    "line_width": 2,            # 线宽
    "color_scheme": "viridis",  # 颜色方案
}

# 评估指标参数
METRICS_CONFIG = {
    "smoothness_weight": 0.3,   # 平滑度权重
    "accuracy_weight": 0.4,     # 准确性权重
    "physics_weight": 0.3,      # 物理合理性权重
    "completeness_weight": 0.2, # 完整性权重
}

# 默认配置
DEFAULT_CONFIG = {
    "interpolation": INTERPOLATION_CONFIG,
    "smoothing": SMOOTHING_CONFIG,
    "physics": PHYSICS_CONFIG,
    "outlier": OUTLIER_CONFIG,
    "kalman": KALMAN_CONFIG,
    "ml": ML_CONFIG,
    "performance": PERFORMANCE_CONFIG,
    "visualization": VISUALIZATION_CONFIG,
    "metrics": METRICS_CONFIG,
}
