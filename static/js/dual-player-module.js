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
        this.isManualControl = false; // 是否正在手动控制帧
        this.videosLoaded = false; // 视频是否已加载
        
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
        this.selectedStrategy = data.selected_strategy || { id: 'auto_fill', name: '自动补齐算法' };
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
                        <span id="currentStrategyName" class="strategy-name">自动补齐算法</span>
                    </div>
                    <div id="strategyDescription" class="strategy-description">左画面显示原始YOLOv8检测结果，右画面显示自动补齐优化结果</div>
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
                        <h4>自动补齐结果</h4>
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
        if (slider) slider.oninput = (e) => {
            this.isManualControl = true;
            this.isPlaying = false;
            this.seekToFrame(parseInt(e.target.value));
        };
        
        console.log('双画面播放器事件绑定完成');
    }

    updateStrategyDisplay() {
        // 更新策略名称显示
        const strategyNameElement = document.getElementById('currentStrategyName');
        const rightTitleElement = document.querySelector('.dual-player-panel:last-child h4');
        
        if (strategyNameElement && this.selectedStrategy) {
            strategyNameElement.textContent = this.selectedStrategy.name || '自动补齐算法';
        }
        
        if (rightTitleElement && this.selectedStrategy) {
            rightTitleElement.textContent = `${this.selectedStrategy.name || '自动补齐'}结果`;
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
                        this.videosLoaded = true;
                        console.log('左视频加载完成');
                    };
                    
                    rightVideo.onloadedmetadata = () => {
                        this.resizeCanvases();
                        this.updateDisplay();
                        console.log('右视频加载完成');
                    };
                    
                    // 同步视频播放（只在播放时同步，避免手动控制时干扰）
                    leftVideo.addEventListener('timeupdate', () => {
                        if (this.isPlaying && !this.isManualControl) {
                            if (rightVideo.currentTime !== leftVideo.currentTime) {
                                rightVideo.currentTime = leftVideo.currentTime;
                            }
                            this.updateFrameInfo();
                        }
                    });
                    
                    rightVideo.addEventListener('timeupdate', () => {
                        if (this.isPlaying && !this.isManualControl) {
                            if (leftVideo.currentTime !== rightVideo.currentTime) {
                                leftVideo.currentTime = rightVideo.currentTime;
                            }
                            this.updateFrameInfo();
                        }
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
        
        if (leftVideo && rightVideo && this.videosLoaded) {
            this.isManualControl = false; // 停止手动控制模式
            leftVideo.play();
            rightVideo.play();
            this.isPlaying = true;
            this.updateButtonStates();
            console.log('开始播放');
        } else {
            console.log('视频未加载完成，无法播放');
        }
    }

    pause() {
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftVideo && rightVideo) {
            leftVideo.pause();
            rightVideo.pause();
            this.isPlaying = false;
            this.isManualControl = false; // 停止手动控制模式
            this.updateButtonStates();
            console.log('暂停播放');
        }
    }

    prevFrame() {
        if (!this.videosLoaded) {
            console.log('视频未加载完成，无法控制帧');
            return;
        }
        
        this.isPlaying = false; // 停止播放
        this.isManualControl = true; // 进入手动控制模式
        this.currentFrame = Math.max(0, this.currentFrame - 1);
        this.seekToFrame(this.currentFrame);
        this.updateButtonStates();
        console.log('上一帧:', this.currentFrame);
    }

    nextFrame() {
        if (!this.videosLoaded) {
            console.log('视频未加载完成，无法控制帧');
            return;
        }
        
        this.isPlaying = false; // 停止播放
        this.isManualControl = true; // 进入手动控制模式
        this.currentFrame = Math.min(this.totalFrames - 1, this.currentFrame + 1);
        this.seekToFrame(this.currentFrame);
        this.updateButtonStates();
        console.log('下一帧:', this.currentFrame);
    }

    seekToFrame(frame) {
        if (!this.videosLoaded) {
            console.log('视频未加载完成，无法跳转帧');
            return;
        }
        
        this.currentFrame = frame;
        const time = frame / this.fps;
        
        const leftVideo = document.getElementById('dualLeftVideo');
        const rightVideo = document.getElementById('dualRightVideo');
        
        if (leftVideo && rightVideo) {
            // 暂停视频以避免timeupdate事件干扰
            leftVideo.pause();
            rightVideo.pause();
            
            leftVideo.currentTime = time;
            rightVideo.currentTime = time;
            
            // 如果正在播放，则继续播放
            if (this.isPlaying) {
                setTimeout(() => {
                    leftVideo.play();
                    rightVideo.play();
                }, 50);
            }
        }
        
        this.updateDisplay();
        this.updateButtonStates();
    }

    updateButtonStates() {
        // 更新按钮状态显示
        const playBtn = document.getElementById('dualPlayBtn');
        const pauseBtn = document.getElementById('dualPauseBtn');
        const prevBtn = document.getElementById('dualPrevBtn');
        const nextBtn = document.getElementById('dualNextBtn');
        
        if (playBtn && pauseBtn && prevBtn && nextBtn) {
            if (this.isPlaying) {
                playBtn.style.opacity = '0.5';
                pauseBtn.style.opacity = '1';
                prevBtn.style.opacity = '0.5';
                nextBtn.style.opacity = '0.5';
            } else if (this.isManualControl) {
                playBtn.style.opacity = '1';
                pauseBtn.style.opacity = '0.5';
                prevBtn.style.opacity = '1';
                nextBtn.style.opacity = '1';
            } else {
                playBtn.style.opacity = '1';
                pauseBtn.style.opacity = '0.5';
                prevBtn.style.opacity = '1';
                nextBtn.style.opacity = '1';
            }
        }
    }

    updateFrameInfo() {
        // 只在播放时根据视频时间更新帧数，手动控制时不更新
        if (this.isPlaying && !this.isManualControl) {
            const leftVideo = document.getElementById('dualLeftVideo');
            if (leftVideo && this.fps > 0) {
                this.currentFrame = Math.floor(leftVideo.currentTime * this.fps);
            }
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
        
        // 更新检测信息（使用新的数据源确保与动态视频分析一致）
        if (this.data) {
            // 左侧：原始检测结果
            const leftDetection = this.data.left_frame_detections?.find(d => d.frame === this.currentFrame) || 
                                 this.data.frame_detections?.find(d => d.frame === this.currentFrame);
            
            // 右侧：补齐后的检测结果
            const rightDetection = this.data.right_frame_detections?.find(d => d.frame === this.currentFrame);
            
            // 更新左侧（原始检测结果）
            const leftStatus = document.getElementById('dualLeftStatus');
            const leftCoords = document.getElementById('dualLeftCoords');
            if (leftStatus && leftCoords) {
                if (leftDetection && leftDetection.detected) {
                    leftStatus.textContent = '状态: 已检测';
                    leftCoords.textContent = `坐标: (${leftDetection.x}, ${leftDetection.y})`;
                } else {
                    leftStatus.textContent = '状态: 未检测';
                    leftCoords.textContent = '坐标: (0, 0)';
                }
            }
            
            // 更新右侧（补齐后的检测结果）
            const rightStatus = document.getElementById('dualRightStatus');
            const rightCoords = document.getElementById('dualRightCoords');
            if (rightStatus && rightCoords) {
                if (rightDetection && rightDetection.detected) {
                    if (rightDetection.is_filled) {
                        rightStatus.textContent = '状态: 已补齐';
                    } else {
                        rightStatus.textContent = '状态: 已检测';
                    }
                    rightCoords.textContent = `坐标: (${rightDetection.x}, ${rightDetection.y})`;
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
            // 使用left_frame_detections获取原始检测结果（与动态视频分析保持一致）
            const detection = this.data.left_frame_detections?.find(d => d.frame === this.currentFrame) || 
                             this.data.frame_detections?.find(d => d.frame === this.currentFrame);
            
            if (detection && detection.detected) {
                // 使用像素坐标，与动态视频分析保持一致
                const videoWidth = this.data.video_info?.width || 720;
                const videoHeight = this.data.video_info?.height || 1280;
                const scaleX = canvas.width / videoWidth;
                const scaleY = canvas.height / videoHeight;
                
                const x = detection.x * scaleX;
                const y = detection.y * scaleY;
                
                // 绘制检测框
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 2;
                ctx.strokeRect(x - 10, y - 10, 20, 20);
                
                // 绘制检测点
                ctx.fillStyle = 'red';
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.fill();
                
                // 绘制置信度
                ctx.fillStyle = 'red';
                ctx.font = 'bold 12px Arial';
                ctx.fillText(`${Math.round(detection.confidence * 100)}%`, x + 15, y - 5);
            }
        }
    }

    drawRightDetections() {
        const canvas = document.getElementById('dualRightCanvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.data) {
            // 使用right_frame_detections获取补齐后的检测结果
            const detection = this.data.right_frame_detections?.find(d => d.frame === this.currentFrame);
            
            if (detection && detection.detected) {
                // 使用像素坐标
                const videoWidth = this.data.video_info?.width || 720;
                const videoHeight = this.data.video_info?.height || 1280;
                const scaleX = canvas.width / videoWidth;
                const scaleY = canvas.height / videoHeight;
                
                const x = detection.x * scaleX;
                const y = detection.y * scaleY;
                
                if (detection.is_filled) {
                    // 补齐的数据（绿色）
                    ctx.strokeStyle = 'green';
                    ctx.fillStyle = 'green';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x - 10, y - 10, 20, 20);
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // 绘制"补齐"标识
                    ctx.font = 'bold 12px Arial';
                    ctx.fillText('补齐', x + 15, y - 5);
                } else {
                    // 原始检测数据（蓝色）
                    ctx.strokeStyle = 'blue';
                    ctx.fillStyle = 'blue';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x - 10, y - 10, 20, 20);
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // 绘制置信度
                    ctx.font = 'bold 12px Arial';
                    ctx.fillText(`${Math.round(detection.confidence * 100)}%`, x + 15, y - 5);
                }
            } else {
                // 没有检测结果，显示未检测
                ctx.fillStyle = 'gray';
                ctx.font = 'bold 12px Arial';
                ctx.fillText('未检测', canvas.width / 2 - 20, canvas.height / 2);
            }
        }
    }
}

// 初始化双画面播放器模块
const dualPlayerModule = new DualPlayerModule();

// 注册到全局作用域
window.dualPlayerModule = dualPlayerModule;
console.log('✅ dualPlayerModule 已创建并加载到全局作用域');
