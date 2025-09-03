// 视频播放器模块
class VideoPlayerModule {
    constructor() {
        this.currentAnalysisData = null;
        this.videoPlayer = null;
        this.overlayCanvas = null;
        this.canvasContext = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 监听结果更新事件
        document.addEventListener('resultsUpdated', (event) => {
            setTimeout(() => {
                // 先确保视频区域已创建
                this.createVideoSection();
                // 然后再设置视频播放器
                setTimeout(() => {
                    this.setupVideoPlayer(event.detail);
                }, 200);
            }, 500);
        });
    }

    createVideoSection() {
        const trajectoryChart = document.getElementById('trajectoryChart');
        if (trajectoryChart && !document.querySelector('.video-container')) {
            const videoSection = document.createElement('div');
            videoSection.className = 'result-card';
            videoSection.innerHTML = `
                <h3>🎥 动态视频分析 - 实时显示杆头点位</h3>
                <div class="video-container">
                    <video id="videoPlayer" controls style="width: 100%; max-width: 800px; height: auto;">
                        您的浏览器不支持视频播放
                    </video>
                    <canvas id="overlayCanvas" class="overlay-canvas"></canvas>
                </div>
                <div class="video-controls">
                    <button id="loadVideoBtn" class="btn btn-primary">加载上传的视频</button>
                    <button id="playPauseBtn" class="btn btn-secondary">播放/暂停</button>
                    <button id="stepForwardBtn" class="btn btn-secondary">前进1帧</button>
                    <button id="stepBackwardBtn" class="btn btn-secondary">后退1帧</button>
                    <span id="currentFrameInfo" style="margin-left: 20px; font-weight: bold;"></span>
                </div>
                <div class="detection-info">
                    <h4>当前帧检测信息</h4>
                    <div id="currentDetectionInfo" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        请先上传视频并开始播放
                    </div>
                </div>
            `;
            trajectoryChart.parentNode.insertBefore(videoSection, trajectoryChart.nextSibling);
        }
    }

    setupVideoPlayer(data) {
        console.log('设置视频播放器:', data);
        this.currentAnalysisData = data;
        
        // 检查DOM元素是否存在
        this.videoPlayer = document.getElementById('videoPlayer');
        this.overlayCanvas = document.getElementById('overlayCanvas');
        
        console.log('查找DOM元素:', {
            videoPlayer: this.videoPlayer,
            overlayCanvas: this.overlayCanvas,
            videoPlayerExists: !!this.videoPlayer,
            overlayCanvasExists: !!this.overlayCanvas
        });
        
        if (!this.videoPlayer || !this.overlayCanvas) {
            console.error('找不到视频播放器或Canvas元素');
            console.log('当前页面上的元素:', {
                videoElements: document.querySelectorAll('video'),
                canvasElements: document.querySelectorAll('canvas'),
                videoPlayerElements: document.querySelectorAll('#videoPlayer'),
                overlayCanvasElements: document.querySelectorAll('#overlayCanvas')
            });
            return;
        }
        
        this.canvasContext = this.overlayCanvas.getContext('2d');
        
        // 设置视频源
        const currentVideoFile = window.uploadModule.getCurrentVideoFile();
        if (currentVideoFile) {
            console.log('设置视频源:', currentVideoFile.name);
            const videoUrl = URL.createObjectURL(currentVideoFile);
            this.videoPlayer.src = videoUrl;
            
            // 监听视频加载完成
            this.videoPlayer.addEventListener('loadedmetadata', () => {
                console.log('视频元数据加载完成');
                this.resizeCanvas();
                this.updateOverlay();
            });
            
            this.videoPlayer.addEventListener('canplay', () => {
                console.log('视频可以播放');
                this.resizeCanvas();
            });
            
            this.videoPlayer.addEventListener('error', (e) => {
                console.error('视频加载错误:', e);
            });
        } else {
            console.error('没有找到上传的视频文件');
        }
        
        // 设置Canvas尺寸
        this.resizeCanvas();
        
        // 监听视频事件
        this.videoPlayer.addEventListener('play', () => {
            console.log('视频开始播放');
            requestAnimationFrame(() => this.updateOverlay());
        });
        
        this.videoPlayer.addEventListener('pause', () => {
            console.log('视频暂停');
            this.updateOverlay();
        });
        
        this.videoPlayer.addEventListener('timeupdate', () => {
            this.updateOverlay();
            this.updateCurrentFrameInfo();
        });
        
        // 设置控制按钮
        this.setupControlButtons();
    }

    setupControlButtons() {
        const loadVideoBtn = document.getElementById('loadVideoBtn');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const stepForwardBtn = document.getElementById('stepForwardBtn');
        const stepBackwardBtn = document.getElementById('stepBackwardBtn');
        
        if (loadVideoBtn) {
            loadVideoBtn.addEventListener('click', () => {
                this.videoPlayer.load();
                this.resizeCanvas();
            });
        }
        
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                if (this.videoPlayer.paused) {
                    this.videoPlayer.play();
                } else {
                    this.videoPlayer.pause();
                }
            });
        }
        
        if (stepForwardBtn) {
            stepForwardBtn.addEventListener('click', () => {
                const fps = this.currentAnalysisData?.video_info?.fps || 30;
                this.videoPlayer.currentTime += 1/fps;
                // 手动触发overlay更新
                setTimeout(() => {
                    this.updateOverlay();
                    this.updateCurrentFrameInfo();
                }, 50);
            });
        }
        
        if (stepBackwardBtn) {
            stepBackwardBtn.addEventListener('click', () => {
                const fps = this.currentAnalysisData?.video_info?.fps || 30;
                this.videoPlayer.currentTime -= 1/fps;
                // 手动触发overlay更新
                setTimeout(() => {
                    this.updateOverlay();
                    this.updateCurrentFrameInfo();
                }, 50);
            });
        }
    }

    resizeCanvas() {
        if (!this.videoPlayer || !this.overlayCanvas) return;
        
        const videoRect = this.videoPlayer.getBoundingClientRect();
        this.overlayCanvas.style.width = videoRect.width + 'px';
        this.overlayCanvas.style.height = videoRect.height + 'px';
        this.overlayCanvas.width = videoRect.width;
        this.overlayCanvas.height = videoRect.height;
    }

    updateOverlay() {
        if (!this.overlayCanvas || !this.currentAnalysisData || !this.videoPlayer) return;
        
        const currentTime = this.videoPlayer.currentTime;
        const fps = this.currentAnalysisData.video_info?.fps || 30;
        const currentFrame = Math.floor(currentTime * fps);
        
        // 清除Canvas
        this.canvasContext.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
        
        // 查找当前帧的检测结果
        const detection = this.currentAnalysisData.frame_detections.find(d => d.frame === currentFrame);
        
        if (detection && detection.detected) {
            // 计算检测框在Canvas上的位置
            const videoWidth = this.currentAnalysisData.video_info.width;
            const videoHeight = this.currentAnalysisData.video_info.height;
            const canvasWidth = this.overlayCanvas.width;
            const canvasHeight = this.overlayCanvas.height;
            
            const scaleX = canvasWidth / videoWidth;
            const scaleY = canvasHeight / videoHeight;
            
            const x = detection.x * scaleX;
            const y = detection.y * scaleY;
            
            // 绘制检测框（绿色方框）
            this.canvasContext.strokeStyle = '#00ff00';
            this.canvasContext.lineWidth = 3;
            this.canvasContext.strokeRect(x - 25, y - 25, 50, 50);
            
            // 绘制中心点
            this.canvasContext.fillStyle = '#ff0000';
            this.canvasContext.beginPath();
            this.canvasContext.arc(x, y, 3, 0, 2 * Math.PI);
            this.canvasContext.fill();
            
            // 绘制置信度文本
            this.canvasContext.fillStyle = '#00ff00';
            this.canvasContext.font = 'bold 14px Arial';
            this.canvasContext.fillText(`${Math.round(detection.confidence * 100)}%`, x + 30, y - 10);
        }
    }

    updateCurrentFrameInfo() {
        if (!this.videoPlayer || !this.currentAnalysisData) return;
        
        const currentTime = this.videoPlayer.currentTime;
        const fps = 30; // 假设30fps
        const currentFrame = Math.floor(currentTime * fps);
        
        const currentFrameInfo = document.getElementById('currentFrameInfo');
        if (currentFrameInfo) {
            currentFrameInfo.textContent = `第 ${currentFrame + 1} 帧 / 共 ${this.currentAnalysisData.total_frames} 帧`;
        }
        
        // 更新检测信息
        const detection = this.currentAnalysisData.frame_detections.find(d => d.frame === currentFrame);
        const detectionInfo = document.getElementById('currentDetectionInfo');
        
        if (detectionInfo) {
            if (detection && detection.detected) {
                detectionInfo.innerHTML = `
                    <p><strong>检测状态:</strong> ✅ 检测到杆头</p>
                    <p><strong>坐标:</strong> X: ${detection.x}, Y: ${detection.y}</p>
                    <p><strong>置信度:</strong> ${Math.round(detection.confidence * 100)}%</p>
                    <p><strong>帧索引:</strong> ${detection.frame}</p>
                `;
            } else {
                detectionInfo.innerHTML = `
                    <p><strong>检测状态:</strong> ❌ 未检测到杆头</p>
                    <p><strong>帧索引:</strong> ${currentFrame}</p>
                `;
            }
        }
    }
}

// 创建全局实例
window.videoPlayerModule = new VideoPlayerModule();
console.log('✅ videoPlayerModule 已创建并加载到全局作用域');
