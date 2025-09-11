// 轨迹图表模块
class TrajectoryModule {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 监听结果更新事件
        document.addEventListener('resultsUpdated', (event) => {
            setTimeout(() => {
                this.createTrajectoryChart(event.detail);
            }, 300);
        });
    }

    createTrajectoryChart(data) {
        const clubHeadInfo = document.getElementById('clubHeadInfo');
        if (!clubHeadInfo) {
            console.log('等待clubHeadInfo创建...');
            setTimeout(() => this.createTrajectoryChart(data), 200);
            return;
        }

        console.log('创建轨迹图表:', { clubHeadInfo, exists: !!clubHeadInfo });

        // 检查是否已存在轨迹图表
        if (document.getElementById('trajectoryChart')) {
            return;
        }

        // 计算Canvas尺寸，保持视频宽高比
        const videoInfo = data.video_info || {};
        const videoWidth = videoInfo.width || 720;
        const videoHeight = videoInfo.height || 1280;
        const videoAspectRatio = videoWidth / videoHeight;
        
        // 设置Canvas最大尺寸
        const maxCanvasWidth = 800;
        const maxCanvasHeight = 400;
        
        let canvasWidth, canvasHeight;
        if (videoAspectRatio > 1) {  // 横屏视频
            canvasWidth = Math.min(maxCanvasWidth, Math.floor(maxCanvasHeight * videoAspectRatio));
            canvasHeight = maxCanvasHeight;
        } else {  // 竖屏视频
            canvasHeight = Math.min(maxCanvasHeight, Math.floor(maxCanvasWidth / videoAspectRatio));
            canvasWidth = Math.floor(canvasHeight * videoAspectRatio);
        }

        console.log(`视频尺寸: ${videoWidth}×${videoHeight}, Canvas尺寸: ${canvasWidth}×${canvasHeight}, 宽高比: ${videoAspectRatio.toFixed(3)}`);

        const trajectoryChart = document.createElement('div');
        trajectoryChart.className = 'trajectory-chart';
        trajectoryChart.id = 'trajectoryChart';
        trajectoryChart.innerHTML = `
            <div class="trajectory-controls" style="margin-bottom: 15px;">
                <label style="margin-right: 15px;">
                    <input type="radio" name="trajectoryType" value="auto_fill" checked> 自动补齐优化
                </label>
                <label>
                    <input type="radio" name="trajectoryType" value="comparison"> 对比显示
                </label>
            </div>
            <div class="canvas-container" style="text-align: center; margin: 10px 0;">
                <canvas id="trajectoryCanvas" width="${canvasWidth}" height="${canvasHeight}" style="border: 1px solid #ddd; border-radius: 4px;"></canvas>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    视频尺寸: ${videoWidth} × ${videoHeight} | Canvas: ${canvasWidth} × ${canvasHeight}
                </div>
            </div>
        `;

        clubHeadInfo.appendChild(trajectoryChart);
        console.log('轨迹图表创建完成:', trajectoryChart);

        // 绘制轨迹
        this.drawTrajectoryChart(data);
        
        // 绑定控制事件
        this.bindTrajectoryControls(data);
    }

    bindTrajectoryControls(data) {
        const controls = document.querySelectorAll('input[name="trajectoryType"]');
        controls.forEach(control => {
            control.addEventListener('change', () => {
                this.drawTrajectoryChart(data);
            });
        });
    }

    drawTrajectoryChart(data) {
        const canvas = document.getElementById('trajectoryCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // 清除画布
        ctx.clearRect(0, 0, width, height);

        // 获取当前选择的轨迹类型
        const selectedType = document.querySelector('input[name="trajectoryType"]:checked')?.value || 'auto_fill';
        
        // 根据选择获取轨迹数据
        let trajectoryData = data.club_head_trajectory; // 默认使用优化后的数据
        let trajectoryLabel = '自动补齐优化数据';
        
        if (selectedType === 'auto_fill') {
            // 使用自动补齐后的数据
            trajectoryData = data.club_head_trajectory; // 这是优化后的数据
            trajectoryLabel = '自动补齐优化数据';
        } else if (selectedType === 'comparison') {
            // 对比显示：显示原始检测数据
            trajectoryData = data.original_trajectory || data.left_view_trajectory;
            trajectoryLabel = '原始检测数据对比';
        }

        // 过滤掉零值坐标（归一化坐标中0,0表示未检测到）
        const validPoints = trajectoryData.filter(point => point[0] > 0 && point[1] > 0);
        
        if (validPoints.length === 0) {
            ctx.fillStyle = '#666';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('没有有效的轨迹数据', width / 2, height / 2);
            return;
        }

        // 归一化坐标直接映射到画布（0-1 映射到 0-canvas_size）
        const padding = 40;
        const drawWidth = width - padding * 2;
        const drawHeight = height - padding * 2;

        console.log('归一化轨迹坐标:', validPoints.slice(0, 5)); // 显示前5个点

        // 绘制坐标轴
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        
        // X轴
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Y轴
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.stroke();

        // 如果是对比模式，绘制三条轨迹
        if (selectedType === 'comparison' && data.optimized_trajectory && data.fast_motion_trajectory) {
            // 绘制原始轨迹（蓝色）
            this.drawTrajectoryLine(ctx, data.club_head_trajectory, '#4facfe', padding, drawWidth, drawHeight, width, height);
            
            // 绘制标准优化轨迹（红色）
            this.drawTrajectoryLine(ctx, data.optimized_trajectory, '#ff4757', padding, drawWidth, drawHeight, width, height);
            
            // 绘制快速移动优化轨迹（绿色）
            this.drawTrajectoryLine(ctx, data.fast_motion_trajectory, '#2ed573', padding, drawWidth, drawHeight, width, height);
            
            // 添加图例
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.textAlign = 'left';
            ctx.fillText('原始数据', padding + 10, padding + 20);
            ctx.fillText('标准优化', padding + 10, padding + 35);
            ctx.fillText('快速移动优化', padding + 10, padding + 50);
            
            // 绘制图例颜色
            ctx.fillStyle = '#4facfe';
            ctx.fillRect(padding, padding + 10, 15, 3);
            ctx.fillStyle = '#ff4757';
            ctx.fillRect(padding, padding + 25, 15, 3);
            ctx.fillStyle = '#2ed573';
            ctx.fillRect(padding, padding + 40, 15, 3);
        } else {
            // 绘制单条轨迹
            let color = '#4facfe'; // 默认蓝色
            if (selectedType === 'optimized') color = '#ff4757'; // 红色
            else if (selectedType === 'fast_motion') color = '#2ed573'; // 绿色
            
            this.drawTrajectoryLine(ctx, trajectoryData, color, padding, drawWidth, drawHeight, width, height);
        }

        // 添加轴标签
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // X轴标签
        ctx.fillText('X坐标 (归一化 0-1)', width / 2, height - 10);
        
        // Y轴标签
        ctx.save();
        ctx.translate(20, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Y坐标 (归一化 0-1)', 0, 0);
        ctx.restore();
        
        // 添加轨迹类型标签
        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'right';
        ctx.fillText(trajectoryLabel, width - padding, padding + 20);
    }

    drawTrajectoryLine(ctx, trajectoryData, color, padding, drawWidth, drawHeight, width, height) {
        const validPoints = trajectoryData.filter(point => point[0] > 0 && point[1] > 0);
        
        if (validPoints.length === 0) return;

        // 绘制轨迹线
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        validPoints.forEach((point, index) => {
            // 归一化坐标 (0-1) 直接映射到画布坐标
            const x = padding + point[0] * drawWidth;
            const y = height - padding - point[1] * drawHeight; // Y轴翻转（图像坐标系）
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // 绘制关键点
        ctx.fillStyle = color;
        validPoints.forEach((point, index) => {
            const x = padding + point[0] * drawWidth;
            const y = height - padding - point[1] * drawHeight;
            
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, 2 * Math.PI);
            ctx.fill();
        });
    }
}

// 创建全局实例
window.trajectoryModule = new TrajectoryModule();
console.log('✅ trajectoryModule 已创建并加载到全局作用域');
