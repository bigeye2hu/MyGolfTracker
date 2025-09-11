// 帧分析模块 - 显示每一帧图片和对应的杆头检测结果
class FrameAnalysisModule {
    constructor() {
        this.currentAnalysisData = null;
        this.frameImages = [];
        this.currentPage = 0;
        this.framesPerPage = 12;
        this.bindEvents();
    }

    bindEvents() {
        // 监听结果更新事件
        document.addEventListener('resultsUpdated', (event) => {
            setTimeout(() => {
                this.createFrameAnalysisSection(event.detail);
            }, 700);
        });
    }

    createFrameAnalysisSection(data) {
        console.log('🔍 FrameAnalysisModule 收到 resultsUpdated 事件');
        this.currentAnalysisData = data;
        
        // 检查是否已存在帧分析区域
        const existingSection = document.querySelector('.frame-analysis-section');
        if (existingSection) {
            console.log('⚠️ 帧分析区域已存在，更新数据并刷新显示');
            // 即使区域已存在，也要更新数据并刷新显示
            this.refreshFrameDisplay();
            return;
        }
        
        console.log('✅ 开始创建帧分析区域');

        // 等待轨迹图表创建完成
        const trajectoryChart = document.getElementById('trajectoryChart');
        if (!trajectoryChart) {
            setTimeout(() => this.createFrameAnalysisSection(data), 200);
            return;
        }

        const frameSection = document.createElement('div');
        frameSection.className = 'result-card frame-analysis-section';
        frameSection.innerHTML = `
            <h3>📸 帧分析 - 查看每一帧的杆头检测结果</h3>
            <div class="frame-controls">
                <button id="prevPageBtn" class="btn btn-secondary">上一页</button>
                <span id="pageInfo" style="margin: 0 20px; font-weight: bold;">第 1 页 / 共 ${Math.ceil(data.total_frames / this.framesPerPage)} 页</span>
                <button id="nextPageBtn" class="btn btn-secondary">下一页</button>
                <button id="showAllFramesBtn" class="btn btn-primary">显示所有帧</button>
            </div>
            <div class="frame-grid" id="frameGrid"></div>
            <div class="frame-details" id="frameDetails" style="display: none;">
                <h4>帧详细信息</h4>
                <div id="frameDetailContent"></div>
            </div>
        `;

        // 插入到轨迹图表之后
        trajectoryChart.parentNode.insertBefore(frameSection, trajectoryChart.nextSibling);
        
        // 绑定控制按钮事件
        this.bindFrameControls();
        
        // 显示第一页
        this.showPage(0);
    }

    bindFrameControls() {
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        const showAllFramesBtn = document.getElementById('showAllFramesBtn');

        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => {
                if (this.currentPage > 0) {
                    this.showPage(this.currentPage - 1);
                }
            });
        }

        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => {
                const maxPage = Math.ceil(this.currentAnalysisData.total_frames / this.framesPerPage) - 1;
                if (this.currentPage < maxPage) {
                    this.showPage(this.currentPage + 1);
                }
            });
        }

        if (showAllFramesBtn) {
            showAllFramesBtn.addEventListener('click', () => {
                this.showAllFrames();
            });
        }
    }

    showPage(pageIndex) {
        this.currentPage = pageIndex;
        const frameGrid = document.getElementById('frameGrid');
        if (!frameGrid) return;

        const startFrame = pageIndex * this.framesPerPage;
        const endFrame = Math.min(startFrame + this.framesPerPage, this.currentAnalysisData.total_frames);
        
        frameGrid.innerHTML = '';
        
        for (let i = startFrame; i < endFrame; i++) {
            const frameCard = this.createFrameCard(i);
            frameGrid.appendChild(frameCard);
        }

        // 更新页码信息
        const pageInfo = document.getElementById('pageInfo');
        if (pageInfo) {
            const totalPages = Math.ceil(this.currentAnalysisData.total_frames / this.framesPerPage);
            pageInfo.textContent = `第 ${pageIndex + 1} 页 / 共 ${totalPages} 页`;
        }

        // 更新按钮状态
        this.updatePageButtonStates();
    }

    createFrameCard(frameIndex) {
        const frameCard = document.createElement('div');
        frameCard.className = 'frame-card';
        
        // 查找该帧的检测结果 - 强制使用优化后的数据
        console.log(`🔍 帧分析模块查找第${frameIndex}帧的检测结果:`);
        console.log('right_frame_detections存在:', !!this.currentAnalysisData.right_frame_detections);
        console.log('right_frame_detections长度:', this.currentAnalysisData.right_frame_detections?.length || 0);
        console.log('frame_detections长度:', this.currentAnalysisData.frame_detections?.length || 0);
        
        // 强制优先使用right_frame_detections
        let detection = null;
        if (this.currentAnalysisData.right_frame_detections) {
            detection = this.currentAnalysisData.right_frame_detections.find(d => d.frame === frameIndex);
            console.log(`从right_frame_detections查找第${frameIndex}帧:`, detection);
        }
        
        if (!detection && this.currentAnalysisData.frame_detections) {
            detection = this.currentAnalysisData.frame_detections.find(d => d.frame === frameIndex);
            console.log(`从frame_detections查找第${frameIndex}帧:`, detection);
        }
        
        console.log(`第${frameIndex}帧最终检测结果:`, detection);
        if (detection) {
            console.log(`  - detected: ${detection.detected}`);
            console.log(`  - is_filled: ${detection.is_filled}`);
            console.log(`  - x: ${detection.x}, y: ${detection.y}`);
            console.log(`  - confidence: ${detection.confidence}`);
        }
        
        if (detection && detection.detected) {
            frameCard.innerHTML = `
                <div class="frame-header">
                    <span class="frame-number">第 ${frameIndex + 1} 帧</span>
                    <span class="detection-status detected">✅ 检测到</span>
                </div>
                <div class="frame-image-placeholder">
                    <div class="frame-coordinates">
                        <strong>坐标(归一化):</strong> X: ${detection.norm_x?.toFixed(4) ?? (detection.x / this.currentAnalysisData.video_info.width).toFixed(4)}, Y: ${detection.norm_y?.toFixed(4) ?? (detection.y / this.currentAnalysisData.video_info.height).toFixed(4)}
                    </div>
                    <div class="frame-confidence">
                        <strong>置信度:</strong> ${Math.round(detection.confidence * 100)}%
                    </div>
                </div>
                <div class="frame-actions">
                    <button class="btn btn-sm btn-primary view-frame-btn" data-frame="${frameIndex}">查看详情</button>
                </div>
            `;
        } else {
            frameCard.innerHTML = `
                <div class="frame-header">
                    <span class="frame-number">第 ${frameIndex + 1} 帧</span>
                    <span class="detection-status not-detected">❌ 未检测到</span>
                </div>
                <div class="frame-image-placeholder">
                    <div class="frame-coordinates">
                        <strong>状态:</strong> 未检测到杆头
                    </div>
                    <div class="frame-confidence">
                        <strong>可能原因:</strong> 杆头超出画面、遮挡、光线不足
                    </div>
                </div>
                <div class="frame-actions">
                    <button class="btn btn-sm btn-secondary view-frame-btn" data-frame="${frameIndex}">查看详情</button>
                </div>
            `;
        }

        // 绑定查看详情事件
        const viewBtn = frameCard.querySelector('.view-frame-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                this.showFrameDetails(frameIndex);
            });
        }

        return frameCard;
    }

    showFrameDetails(frameIndex) {
        const frameDetails = document.getElementById('frameDetails');
        const frameDetailContent = document.getElementById('frameDetailContent');
        
        if (!frameDetails || !frameDetailContent) return;

        // 查找该帧的检测结果 - 使用优化后的数据
        console.log(`🔍 详情页查找第${frameIndex}帧的检测结果:`);
        console.log('right_frame_detections:', this.currentAnalysisData.right_frame_detections?.length || 0);
        console.log('frame_detections:', this.currentAnalysisData.frame_detections?.length || 0);
        
        const detection = this.currentAnalysisData.right_frame_detections?.find(d => d.frame === frameIndex) ||
                         this.currentAnalysisData.frame_detections?.find(d => d.frame === frameIndex);
        
        console.log(`第${frameIndex}帧详情检测结果:`, detection);
        
        if (detection && detection.detected) {
            frameDetailContent.innerHTML = `
                <div class="frame-detail-info">
                    <h5>第 ${frameIndex + 1} 帧检测详情</h5>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>检测状态:</strong> ✅ 成功检测到杆头
                        </div>
                        <div class="detail-item">
                            <strong>X坐标(归一化):</strong> ${(detection.norm_x ?? (detection.x / this.currentAnalysisData.video_info.width)).toFixed(6)}
                        </div>
                        <div class="detail-item">
                            <strong>Y坐标(归一化):</strong> ${(detection.norm_y ?? (detection.y / this.currentAnalysisData.video_info.height)).toFixed(6)}
                        </div>
                        <div class="detail-item">
                            <strong>置信度:</strong> ${Math.round(detection.confidence * 100)}%
                        </div>
                        <div class="detail-item">
                            <strong>视频尺寸:</strong> ${this.currentAnalysisData.video_info.width} × ${this.currentAnalysisData.video_info.height}
                        </div>
                        <div class="detail-item">
                            <strong>相对位置:</strong> X: ${Math.round(detection.x / this.currentAnalysisData.video_info.width * 100)}%, Y: ${Math.round(detection.y / this.currentAnalysisData.video_info.height * 100)}%
                        </div>
                    </div>
                </div>
            `;
        } else {
            frameDetailContent.innerHTML = `
                <div class="frame-detail-info">
                    <h5>第 ${frameIndex + 1} 帧检测详情</h5>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>检测状态:</strong> ❌ 未检测到杆头
                        </div>
                        <div class="detail-item">
                            <strong>可能原因分析:</strong>
                        </div>
                        <div class="detail-item">
                            <ul>
                                <li>杆头超出视频画面范围</li>
                                <li>杆头被其他物体遮挡</li>
                                <li>光线条件不足，对比度低</li>
                                <li>杆头移动速度过快，产生运动模糊</li>
                                <li>YOLOv8模型对该帧的置信度低于阈值</li>
                            </ul>
                        </div>
                        <div class="detail-item">
                            <strong>建议:</strong> 检查视频拍摄角度、光线条件，或调整模型检测阈值
                        </div>
                    </div>
                </div>
            `;
        }

        frameDetails.style.display = 'block';
        frameDetails.scrollIntoView({ behavior: 'smooth' });
    }

    showAllFrames() {
        const frameGrid = document.getElementById('frameGrid');
        if (!frameGrid) return;

        frameGrid.innerHTML = '';
        
        for (let i = 0; i < this.currentAnalysisData.total_frames; i++) {
            const frameCard = this.createFrameCard(i);
            frameCard.style.width = '200px'; // 缩小卡片尺寸以显示更多
            frameGrid.appendChild(frameCard);
        }

        // 隐藏分页控制
        const frameControls = document.querySelector('.frame-controls');
        if (frameControls) {
            frameControls.style.display = 'none';
        }
    }
    
    refreshFrameDisplay() {
        console.log('🔄 刷新帧显示，使用新数据');
        if (!this.currentAnalysisData) {
            console.log('❌ 没有分析数据，无法刷新');
            return;
        }
        
        // 重新渲染当前页的帧
        this.renderCurrentPage();
    }

    updatePageButtonStates() {
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        const totalPages = Math.ceil(this.currentAnalysisData.total_frames / this.framesPerPage);

        if (prevPageBtn) {
            prevPageBtn.disabled = this.currentPage === 0;
        }

        if (nextPageBtn) {
            nextPageBtn.disabled = this.currentPage === totalPages - 1;
        }
    }
}

// 创建全局实例
window.frameAnalysisModule = new FrameAnalysisModule();
console.log('✅ frameAnalysisModule 已创建并加载到全局作用域');
