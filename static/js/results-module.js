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
        
        // 创建失败帧下载区域
        this.displayFailureFramesDownload(data);

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

    displayFailureFramesDownload(data) {
        const resultsSection = document.getElementById('resultsSection');
        
        // 计算失败帧数量
        const failureFrames = data.club_head_trajectory.filter(point => point[0] === 0 && point[1] === 0).length;
        const failureRate = ((failureFrames / data.total_frames) * 100).toFixed(1);
        
        // 只有当有失败帧时才显示下载区域
        if (failureFrames > 0) {
            const failureDownload = document.createElement('div');
            failureDownload.id = 'failureDownload';
            failureDownload.className = 'result-card';
            failureDownload.innerHTML = `
                <h3>🎯 检测失败帧下载</h3>
                <div class="failure-info">
                    <div class="failure-stats">
                        <div class="failure-stat">
                            <strong>失败帧数:</strong> ${failureFrames} 帧
                        </div>
                        <div class="failure-stat">
                            <strong>失败率:</strong> ${failureRate}%
                        </div>
                    </div>
                    <div class="failure-description">
                        <p>检测到 ${failureFrames} 帧未能识别到杆头位置。这些帧的图片可用于模型训练数据增强，提高检测准确率。</p>
                    </div>
                    <div class="download-actions">
                        <a href="${data.failure_download_url || '#'}" 
                           class="download-btn" 
                           target="_blank"
                           ${!data.failure_download_url ? 'style="opacity: 0.5; pointer-events: none;"' : ''}>
                            📥 下载失败帧图片
                        </a>
                        ${data.failure_download_url ? '' : '<span class="download-status">正在生成下载页面...</span>'}
                    </div>
                </div>
            `;
            
            resultsSection.appendChild(failureDownload);
            console.log('创建失败帧下载区域:', failureDownload);

            // 如果后端还未生成链接，则使用 job_id 继续轮询状态接口，生成后即时更新按钮
            if (!data.failure_download_url && data.job_id) {
                let tries = 0;
                const maxTries = 60; // 最长轮询 2 分钟（60 * 2s）
                const intervalId = setInterval(async () => {
                    tries++;
                    try {
                        const r = await fetch(`/analyze/video/status?job_id=${data.job_id}`);
                        if (r.ok) {
                            const j = await r.json();
                            if (j && j.status === 'done' && j.result && j.result.failure_download_url) {
                                clearInterval(intervalId);
                                const a = failureDownload.querySelector('.download-actions a.download-btn') || failureDownload.querySelector('.download-btn');
                                const statusSpan = failureDownload.querySelector('.download-status');
                                if (a) {
                                    a.href = j.result.failure_download_url;
                                    a.style.opacity = '';
                                    a.style.pointerEvents = '';
                                }
                                if (statusSpan) statusSpan.remove();
                                console.log('失败帧下载链接已就绪:', j.result.failure_download_url);
                            }
                        }
                    } catch (e) {
                        console.warn('检查失败帧下载链接时出错', e);
                    }
                    if (tries >= maxTries) clearInterval(intervalId);
                }, 2000);
            }
        }
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
