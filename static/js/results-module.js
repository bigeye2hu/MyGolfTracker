// 结果显示模块
class ResultsModule {
    constructor() {
        this.currentAnalysisData = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 监听分析完成事件
        document.addEventListener('analysisComplete', (event) => {
            console.log('收到分析完成事件:', event.detail);
            this.displayResults(event.detail);
        });
    }

    displayResults(data) {
        this.currentAnalysisData = data;
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) return;

        // 显示结果区域
        resultsSection.style.display = 'block';

        // 创建检测统计区域
        this.displayDetectionStats(data);
        
        // 创建杆头信息区域
        this.displayClubHeadInfo(data);

        // 触发模块更新事件
        this.triggerModulesUpdate();
    }

    displayDetectionStats(data) {
        const resultsSection = document.getElementById('resultsSection');
        
        const detectionStats = document.createElement('div');
        detectionStats.id = 'detectionStats';
        detectionStats.className = 'result-card';
        detectionStats.innerHTML = `
            <h3>📊 检测统计</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <strong>总帧数:</strong> ${data.total_frames}
                </div>
                <div class="stat-item">
                    <strong>检测帧数:</strong> ${data.detected_frames}
                </div>
                <div class="stat-item">
                    <strong>检测率:</strong> ${data.detection_rate}%
                </div>
                <div class="stat-item">
                    <strong>平均置信度:</strong> ${data.avg_confidence}
                </div>
            </div>
        `;
        
        resultsSection.appendChild(detectionStats);
        console.log('创建检测统计区域:', detectionStats);
    }

    displayClubHeadInfo(data) {
        const resultsSection = document.getElementById('resultsSection');
        
        const clubHeadInfo = document.createElement('div');
        clubHeadInfo.id = 'clubHeadInfo';
        clubHeadInfo.className = 'result-card';
        
        // 计算轨迹范围
        const xCoords = data.club_head_trajectory.map(point => point[0]).filter(x => x > 0);
        const yCoords = data.club_head_trajectory.map(point => point[1]).filter(y => y > 0);
        
        const minX = xCoords.length > 0 ? Math.min(...xCoords) : 0;
        const maxX = xCoords.length > 0 ? Math.max(...xCoords) : 0;
        const minY = yCoords.length > 0 ? Math.min(...yCoords) : 0;
        const maxY = yCoords.length > 0 ? Math.max(...yCoords) : 0;
        
        clubHeadInfo.innerHTML = `
            <h3>🏌️ 杆头轨迹信息</h3>
            <div class="trajectory-info">
                <div class="info-grid">
                    <div class="info-item">
                        <strong>轨迹范围:</strong> X: ${minX} - ${maxX}, Y: ${minY} - ${maxY}
                    </div>
                    <div class="info-item">
                        <strong>视频尺寸:</strong> ${data.video_info.width} × ${data.video_info.height}
                    </div>
                    <div class="info-item">
                        <strong>视频帧率:</strong> ${data.video_info.fps} fps
                    </div>
                </div>
            </div>
        `;
        
        resultsSection.appendChild(clubHeadInfo);
        console.log('创建杆头信息区域:', clubHeadInfo);
    }

    triggerModulesUpdate() {
        // 触发结果更新事件，通知其他模块
        setTimeout(() => {
            const event = new CustomEvent('resultsUpdated', {
                detail: this.currentAnalysisData || {}
            });
            document.dispatchEvent(event);
        }, 100);
    }
}

// 创建全局实例
window.resultsModule = new ResultsModule();
console.log('✅ resultsModule 已创建并加载到全局作用域');
