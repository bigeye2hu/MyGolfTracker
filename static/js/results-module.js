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
        console.log('ResultsModule 收到数据:', data);
        console.log('job_id:', data.job_id);
        this.currentAnalysisData = data;
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) return;

        // 显示结果区域
        resultsSection.style.display = 'block';

        // 创建检测统计区域
        this.displayDetectionStats(data);
        
        // 创建杆头信息区域
        this.displayClubHeadInfo(data);
        
        // 创建训练数据收集区域
        this.displayTrainingDataCollection(data);

        // 触发挥杆状态可视化
        this.triggerSwingVisualization(data);

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
                <div class="stat-item">
                    <strong>分析分辨率:</strong> ${data.analysis_resolution || '960×960'}
                </div>
                <div class="stat-item">
                    <strong>原始视频尺寸:</strong> ${data.video_width || '未知'}×${data.video_height || '未知'}
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

    displayTrainingDataCollection(data) {
        console.log('创建训练数据收集区域...');
        console.log('训练数据收集 - 完整数据:', data);
        console.log('训练数据收集 - job_id:', data.job_id);
        console.log('训练数据收集 - job_id类型:', typeof data.job_id);
        console.log('训练数据收集 - job_id字符串化:', String(data.job_id));
        console.log('训练数据收集 - job_id JSON:', JSON.stringify(data.job_id));
        const resultsSection = document.getElementById('resultsSection');
        
        // 计算训练数据统计
        const failureFrames = data.club_head_trajectory.filter(point => point[0] === 0 && point[1] === 0).length;
        const lowConfidenceFrames = data.low_confidence_frames || 0;
        const totalTrainingFrames = failureFrames + lowConfidenceFrames;
        const failureRate = ((failureFrames / data.total_frames) * 100).toFixed(1);
        const lowConfidenceRate = ((lowConfidenceFrames / data.total_frames) * 100).toFixed(1);
        const totalTrainingRate = ((totalTrainingFrames / data.total_frames) * 100).toFixed(1);
        
        // 只有当有训练数据时才显示收集区域
        if (totalTrainingFrames > 0) {
            const trainingData = document.createElement('div');
            trainingData.id = 'trainingData';
            trainingData.className = 'result-card';
            trainingData.innerHTML = `
                <h3>🎯 训练数据收集</h3>
                <div class="training-info">
                    <div class="training-stats">
                        <div class="stat-grid">
                            <div class="stat-item failure">
                                <div class="stat-number">${failureFrames}</div>
                                <div class="stat-label">失败帧数</div>
                            </div>
                            <div class="stat-item low-confidence">
                                <div class="stat-number">${lowConfidenceFrames}</div>
                                <div class="stat-label">低置信度帧数</div>
                            </div>
                            <div class="stat-item total">
                                <div class="stat-number">${totalTrainingFrames}</div>
                                <div class="stat-label">总训练帧数</div>
                            </div>
                        </div>
                        <div class="training-rates">
                            <span class="rate-item">失败率: ${failureRate}%</span>
                            <span class="rate-item">低置信度率: ${lowConfidenceRate}%</span>
                            <span class="rate-item">总训练数据率: ${totalTrainingRate}%</span>
                        </div>
                    </div>
                    <div class="training-description">
                        <p>收集了 ${totalTrainingFrames} 帧训练数据，包括失败帧和低置信度帧。这些图片可用于模型训练数据增强，提高检测准确率。</p>
                    </div>
                    <div class="download-actions">
                        <a href="${data.training_data_url || '#'}" 
                           class="download-btn" 
                           target="_blank"
                           ${!data.training_data_url ? 'style="opacity: 0.5; pointer-events: none;"' : ''}>
                            📥 下载训练数据图片
                        </a>
                        <a href="${data.training_data_url || '#'}" 
                           class="download-btn secondary" 
                           target="_blank"
                           ${!data.training_data_url ? 'style="opacity: 0.5; pointer-events: none;"' : ''}>
                            👁️ 查看训练数据页面
                        </a>
                        <button class="download-btn zip-btn" 
                                id="downloadZipBtn"
                                data-job-id="${String(data.job_id || '')}"
                                ${!data.training_data_url ? 'disabled' : ''}>
                            📦 下载ZIP包
                        </button>
                        ${data.training_data_url ? '' : '<span class="download-status">正在生成训练数据收集页面...</span>'}
                    </div>
                </div>
            `;
            
            resultsSection.appendChild(trainingData);
            console.log('创建训练数据收集区域:', trainingData);
            
            // 绑定ZIP下载按钮事件
            const downloadZipBtn = document.getElementById('downloadZipBtn');
            console.log('查找ZIP下载按钮:', downloadZipBtn);
            if (downloadZipBtn) {
                const jobIdFromAttr = downloadZipBtn.getAttribute('data-job-id');
                console.log('按钮的data-job-id属性:', jobIdFromAttr);
                downloadZipBtn.addEventListener('click', function() {
                    const jobId = this.getAttribute('data-job-id');
                    console.log('ZIP下载按钮点击，jobId:', jobId);
                    downloadTrainingDataZip(jobId);
                });
            } else {
                console.error('找不到ZIP下载按钮元素');
            }

            // 如果后端还未生成链接，则使用 job_id 继续轮询状态接口，生成后即时更新按钮
            if (!data.training_data_url && data.job_id) {
                let tries = 0;
                const maxTries = 60; // 最长轮询 2 分钟（60 * 2s）
                const intervalId = setInterval(async () => {
                    tries++;
                    try {
                        const r = await fetch(`/analyze/video/status?job_id=${data.job_id}`);
                        if (r.ok) {
                            const j = await r.json();
                            if (j && j.status === 'done' && j.result && j.result.training_data_url) {
                                clearInterval(intervalId);
                                const buttons = trainingData.querySelectorAll('.download-actions a.download-btn');
                                const statusSpan = trainingData.querySelector('.download-status');
                                buttons.forEach(button => {
                                    button.href = j.result.training_data_url;
                                    button.style.opacity = '';
                                    button.style.pointerEvents = '';
                                });
                                if (statusSpan) statusSpan.remove();
                                console.log('训练数据收集链接已就绪:', j.result.training_data_url);
                            }
                        }
                    } catch (e) {
                        console.warn('检查训练数据收集链接时出错', e);
                    }
                    if (tries >= maxTries) clearInterval(intervalId);
                }, 2000);
            }
        }
    }

    triggerSwingVisualization(data) {
        // 触发挥杆状态可视化
        if (window.swingVisualizationModule) {
            console.log('触发挥杆状态可视化...');
            window.swingVisualizationModule.renderSwingVisualization(data);
        } else {
            console.warn('挥杆状态可视化模块未加载');
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

// 添加ZIP下载函数到全局作用域
window.downloadTrainingDataZip = function(jobId) {
    console.log('尝试下载ZIP包，jobId:', jobId);
    console.log('jobId类型:', typeof jobId);
    console.log('jobId字符串化:', String(jobId));
    console.log('jobId JSON:', JSON.stringify(jobId));
    
    if (!jobId || jobId === 'undefined' || jobId === 'null') {
        console.error('jobId无效:', jobId);
        alert('无法下载ZIP包：任务ID无效');
        return;
    }
    
    const zipUrl = `/analyze/training-data/zip/${jobId}`;
    console.log('ZIP下载URL:', zipUrl);
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = zipUrl;
    link.download = `training_data_${jobId}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

// 创建全局实例
window.resultsModule = new ResultsModule();
console.log('✅ resultsModule 已创建并加载到全局作用域');
