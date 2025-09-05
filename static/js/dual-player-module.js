// 双画面播放器模块 - 简化版本，直接绑定用户选择的策略
class DualPlayerModule {
    constructor() {
        this.data = null;
        this.currentFrame = 0;
        this.totalFrames = 0;
        this.fps = 30;
        this.isPlaying = false;
        this.videoUrl = null;
        this.selectedStrategy = null; // 用户选择的策略
        
        this.init();
    }

    init() {
        console.log('DualPlayerModule 初始化');
        
        // 监听分析完成事件
        document.addEventListener('analysisComplete', (e) => {
            console.log('双画面模块收到数据');
            this.handleData(e.detail);
        });
    }

    handleData(data) {
        console.log('处理数据:', data);
        this.data = data;
        this.totalFrames = data.total_frames || 0;
        this.fps = data.video_info?.fps || 30;
        
        // 获取用户选择的策略
        this.selectedStrategy = data.selected_strategy || { id: 'original', name: '原始检测' };
        console.log('用户选择的策略:', this.selectedStrategy);
        
        // 创建双画面播放器UI
        this.createDualPlayerUI();
        
        // 更新策略显示
        this.updateStrategyDisplay();
    }

    createDualPlayerUI() {
        // 查找结果区域
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) {
            console.log('未找到结果区域');
            return;
        }

        // 检查是否已经存在双画面播放器
        if (document.getElementById('dualPlayerSection')) {
            console.log('双画面播放器已存在');
            return;
        }

        // 创建双画面播放器HTML
        const dualPlayerHTML = `
            <div id="dualPlayerSection" class="result-card">
                <h3>🎯 双画面对比</h3>
                
                <div class="dual-player-controls">
                    <button id="dualPlayBtn" class="btn btn-primary">播放</button>
                    <button id="dualPauseBtn" class="btn btn-secondary">暂停</button>
                    <button id="dualPrevBtn" class="btn btn-secondary">上一帧</button>
                    <button id="dualNextBtn" class="btn btn-secondary">下一帧</button>
                    <span class="dual-frame-info">帧: <span id="dualFrameNum">0</span>/<span id="dualTotalFrames">0</span></span>
                </div>
                
                <div class="dual-strategy-info">
                    <div class="strategy-display">
                        <span class="strategy-label">当前策略:</span>
                        <span id="currentStrategyName" class="strategy-name">原始检测</span>
                    </div>
                    <div id="strategyDescription" class="strategy-description">左画面显示原始YOLOv8检测结果，右画面显示用户选择的策略优化结果</div>
                </div>
                
                <div class="dual-player-container">
                    <div class="dual-player-panel">
                        <h4>原始结果</h4>
                        <div class="dual-video-wrapper">
                            <video id="dualLeftVideo" class="dual-video" muted></video>
                            <canvas id="dualLeftCanvas" class="dual-canvas"></canvas>
                        </div>
                        <div class="dual-status">
                            <div id="dualLeftStatus" class="status-info">状态: 等待数据</div>
                            <div id="dualLeftCoords" class="coords-info">坐标: (0, 0)</div>
                        </div>
                    </div>
                    
                    <div class="dual-player-panel">
                        <h4>优化策略结果</h4>
                        <div class="dual-video-wrapper">
                            <video id="dualRightVideo" class="dual-video" muted></video>
                            <canvas id="dualRightCanvas" class="dual-canvas"></canvas>
                        </div>
                        <div class="dual-status">
                            <div id="dualRightStatus" class="status-info">状态: 等待数据</div>
                            <div id="dualRightCoords" class="coords-info">坐标: (0, 0)</div>
                        </div>
                    </div>
                </div>
                
                <div class="dual-frame-control">
                    <input type="range" id="dualFrameSlider" min="0" max="0" value="0" class="frame-slider">
                </div>
            </div>
        `;

        // 插入到结果区域
        resultsSection.insertAdjacentHTML('beforeend', dualPlayerHTML);
        
        // 绑定事件
        this.bindEvents();
        
        // 设置视频
        this.setupVideos();
        
        console.log('双画面播放器UI创建完成');
    }

    bindEvents() {
        const playBtn = document.getElementById('dualPlayBtn');
        const pauseBtn = document.getElementById('dualPauseBtn');
        const prevBtn = document.getElementById('dualPrevBtn');
        const nextBtn = document.getElementById('dualNextBtn');
        const slider = document.getElementById('dualFrameSlider');
        
        if (playBtn) playBtn.onclick = () => this.play();
        if (pauseBtn) pauseBtn.onclick = () => this.pause();
        if (prevBtn) prevBtn.onclick = () => this.prevFrame();
        if (nextBtn) nextBtn.onclick = () => this.nextFrame();
        if (slider) slider.oninput = (e) => this.seekToFrame(parseInt(e.target.value));
        
        console.log('双画面播放器事件绑定完成');
    }

    updateStrategyDisplay() {
        // 更新策略名称显示
        const strategyNameElement = document.getElementById('currentStrategyName');
        const rightTitleElement = document.querySelector('.dual-player-panel:last-child h4');
        
        if (strategyNameElement && this.selectedStrategy) {
            strategyNameElement.textContent = this.selectedStrategy.name || '原始检测';
        }
        
        if (rightTitleElement && this.selectedStrategy) {
            rightTitleElement.textContent = `${this.selectedStrategy.name || '优化策略'}结果`;
        }
    }

    setupVideos() {
        const uploadModule = window.uploadModule;
        if (uploadModule) {
            const videoFile = uploadModule.getCurrentVideoFile();
            if (videoFile) {
                this.videoUrl = URL.createObjectURL(videoFile);
                console.log('设置双画面视频:', videoFile.name);
                
                const leftVideo = document.getElementById('dualLeftVideo');
                const rightVideo = document.getElementById('dualRightVideo');
                
                if (leftVideo && rightVideo) {
                    leftVideo.src = this.videoUrl;
                    rightVideo.src = this.videoUrl;
                    
                    // 等待视频加载
                    leftVideo.onloadedmetadata = () => {
                        this.resizeCanvases();
                        this.updateDisplay();
                    };
                    
                    rightVideo.onloadedmetadata = () => {
                        this.resizeCanvases();
                        this.updateDisplay();
                    };
                    
                    // 同步视频播放
                    leftVideo.addEventListener('timeupdate', () => {
                        if (rightVideo.currentTime !== leftVideo.currentTime) {
                            rightVideo.currentTime = leftVideo.currentTime;
                        }
                        this.updateFrameInfo();
                    });
                    
                    rightVideo.addEventListener('timeupdate', () => {
                        if (leftVideo.currentTime !== rightVideo.currentTime) {
                            leftVideo.currentTime = rightVideo.currentTime;
                        }
                        this.updateFrameInfo();
                    });
                }
            }
        }
    }

    resizeCanvases() {
        const leftCanvas = document.getElementById('dualLeftCanvas');
        const rightCanvas = document.getElementById('dualRightCanvas');
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftCanvas && leftVideo) {
            leftCanvas.width = leftVideo.videoWidth;
            leftCanvas.height = leftVideo.videoHeight;
            leftCanvas.style.width = leftVideo.videoWidth + 'px';
            leftCanvas.style.height = leftVideo.videoHeight + 'px';
        }
        
        if (rightCanvas && rightVideo) {
            rightCanvas.width = rightVideo.videoWidth;
            rightCanvas.height = rightVideo.videoHeight;
            rightCanvas.style.width = rightVideo.videoWidth + 'px';
            rightCanvas.style.height = rightVideo.videoHeight + 'px';
        }
    }

    getOptimizedTrajectory() {
        if (!this.data) return [];
        
        // 直接使用用户选择的策略结果
        return this.data.right_view_trajectory || this.data.club_head_trajectory || [];
    }
    
    getOriginalTrajectory() {
        if (!this.data) return [];
        
        // 使用新的数据字段：左画面永远显示原始YOLOv8检测结果
        return this.data.left_view_trajectory || this.data.original_trajectory || [];
    }

    play() {
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftVideo && rightVideo) {
            leftVideo.play();
            rightVideo.play();
            this.isPlaying = true;
        }
    }

    pause() {
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftVideo && rightVideo) {
            leftVideo.pause();
            rightVideo.pause();
            this.isPlaying = false;
        }
    }

    prevFrame() {
        this.currentFrame = Math.max(0, this.currentFrame - 1);
        this.seekToFrame(this.currentFrame);
    }

    nextFrame() {
        this.currentFrame = Math.min(this.totalFrames - 1, this.currentFrame + 1);
        this.seekToFrame(this.currentFrame);
    }

    seekToFrame(frame) {
        this.currentFrame = frame;
        const time = frame / this.fps;
        
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftVideo && rightVideo) {
            leftVideo.currentTime = time;
            rightVideo.currentTime = time;
        }
        
        this.updateDisplay();
    }

    updateFrameInfo() {
        // 根据视频当前时间计算当前帧
        const leftVideo = document.getElementById('dualLeftVideo');
        if (leftVideo && this.fps > 0) {
            this.currentFrame = Math.floor(leftVideo.currentTime * this.fps);
        }
        
        const frameNum = document.getElementById('dualFrameNum');
        const totalFrames = document.getElementById('dualTotalFrames');
        const slider = document.getElementById('dualFrameSlider');
        
        if (frameNum) frameNum.textContent = this.currentFrame;
        if (totalFrames) totalFrames.textContent = this.totalFrames;
        if (slider) {
            slider.max = this.totalFrames - 1;
            slider.value = this.currentFrame;
        }
        
        // 更新检测信息
        if (this.data) {
            const originalTrajectory = this.getOriginalTrajectory();
            const optimizedTrajectory = this.getOptimizedTrajectory();
            
            const originalPoint = originalTrajectory[this.currentFrame];
            const optimizedPoint = optimizedTrajectory[this.currentFrame];
            
            // 更新左侧
            const leftStatus = document.getElementById('dualLeftStatus');
            const leftCoords = document.getElementById('dualLeftCoords');
            if (leftStatus && leftCoords) {
                if (originalPoint && originalPoint[0] !== 0 && originalPoint[1] !== 0) {
                    leftStatus.textContent = '状态: 已检测';
                    leftCoords.textContent = `坐标: (${originalPoint[0].toFixed(4)}, ${originalPoint[1].toFixed(4)})`;
                } else {
                    leftStatus.textContent = '状态: 未检测';
                    leftCoords.textContent = '坐标: (0, 0)';
                }
            }
            
            // 更新右侧
            const rightStatus = document.getElementById('dualRightStatus');
            const rightCoords = document.getElementById('dualRightCoords');
            if (rightStatus && rightCoords) {
                if (optimizedPoint && optimizedPoint[0] !== 0 && optimizedPoint[1] !== 0) {
                    rightStatus.textContent = '状态: 已检测';
                    rightCoords.textContent = `坐标: (${optimizedPoint[0].toFixed(4)}, ${optimizedPoint[1].toFixed(4)})`;
                } else {
                    rightStatus.textContent = '状态: 未检测';
                    rightCoords.textContent = '坐标: (0, 0)';
                }
            }
        }
    }

    updateDisplay() {
        this.updateFrameInfo();
        this.drawDetections();
    }

    drawDetections() {
        this.drawLeftDetections();
        this.drawRightDetections();
    }

    drawLeftDetections() {
        const canvas = document.getElementById('dualLeftCanvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.data) {
            const originalTrajectory = this.getOriginalTrajectory();
            const point = originalTrajectory[this.currentFrame];
            
            if (point && point[0] !== 0 && point[1] !== 0) {
                const x = point[0] * canvas.width;
                const y = point[1] * canvas.height;
                
                // 绘制检测框
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 2;
                ctx.strokeRect(x - 10, y - 10, 20, 20);
                
                // 绘制检测点
                ctx.fillStyle = 'red';
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }

    drawRightDetections() {
        const canvas = document.getElementById('dualRightCanvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.data) {
            const optimizedTrajectory = this.getOptimizedTrajectory();
            const point = optimizedTrajectory[this.currentFrame];
            
            if (point && point[0] !== 0 && point[1] !== 0) {
                const x = point[0] * canvas.width;
                const y = point[1] * canvas.height;
                
                // 绘制检测框
                ctx.strokeStyle = 'blue';
                ctx.lineWidth = 2;
                ctx.strokeRect(x - 10, y - 10, 20, 20);
                
                // 绘制检测点
                ctx.fillStyle = 'blue';
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }
}

// 初始化双画面播放器模块
const dualPlayerModule = new DualPlayerModule();
