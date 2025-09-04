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
                    <video id="videoPlayer" controls style="width: 100%; max-width: 800px; height: auto;" preload="metadata" playsinline>
                        您的浏览器不支持视频播放
                    </video>
                    <canvas id="overlayCanvas" class="overlay-canvas"></canvas>
                    <div id="videoInfo" style="margin-top: 10px; font-size: 12px; color: #666;">
                        视频信息将在这里显示
                    </div>
                    <div id="formatWarning" style="margin-top: 10px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; display: none;">
                        <strong>⚠️ 视频格式提示:</strong> 如果视频显示异常，请尝试将MOV文件转换为MP4格式。推荐使用H.264编码的MP4文件以获得最佳兼容性。
                        <br><br>
                        <strong>🔧 解决方案:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li><strong>推荐：</strong><a href="/convert/test-page" target="_blank" style="color: #007bff; text-decoration: none;">使用我们的转换服务</a> - 一键转换，简单快捷</li>
                            <li>使用FFmpeg转换: <code>ffmpeg -i input.mov -c:v libx264 output.mp4</code></li>
                            <li>使用在线转换工具 (CloudConvert, Convertio等)</li>
                            <li>使用视频编辑软件重新导出为MP4格式</li>
                        </ul>
                    </div>
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
        console.log('检查uploadModule:', window.uploadModule);
        const currentVideoFile = window.uploadModule ? window.uploadModule.getCurrentVideoFile() : null;
        console.log('获取到的视频文件:', currentVideoFile);
        
        if (currentVideoFile) {
            console.log('设置视频源:', currentVideoFile.name, currentVideoFile.type, currentVideoFile.size);
            
            // 验证视频文件
            console.log('视频文件验证:', {
                name: currentVideoFile.name,
                type: currentVideoFile.type,
                size: currentVideoFile.size,
                lastModified: currentVideoFile.lastModified
            });
            
            // 检查文件类型
            if (!currentVideoFile.type.startsWith('video/')) {
                console.warn('文件类型可能不是视频:', currentVideoFile.type);
            }
            
            // 检查文件大小
            if (currentVideoFile.size === 0) {
                console.error('视频文件大小为0，可能已损坏');
                const videoInfo = document.getElementById('videoInfo');
                if (videoInfo) {
                    videoInfo.innerHTML = '<span style="color: red;">❌ 视频文件大小为0，可能已损坏</span>';
                }
                return;
            }
            
            // 清理之前的URL
            if (this.videoPlayer.src && this.videoPlayer.src.startsWith('blob:')) {
                URL.revokeObjectURL(this.videoPlayer.src);
            }
            
            try {
                const videoUrl = URL.createObjectURL(currentVideoFile);
                console.log('创建的视频URL:', videoUrl);
                this.videoPlayer.src = videoUrl;
                
                // 添加加载状态监听
                this.videoPlayer.addEventListener('loadstart', () => {
                    console.log('开始加载视频');
                });
                
                this.videoPlayer.addEventListener('loadeddata', () => {
                    console.log('视频数据加载完成');
                });
                
            } catch (error) {
                console.error('创建视频URL失败:', error);
                const videoInfo = document.getElementById('videoInfo');
                if (videoInfo) {
                    videoInfo.innerHTML = '<span style="color: red;">❌ 无法创建视频URL</span>';
                }
            }
            
            // 监听视频加载完成
            this.videoPlayer.addEventListener('loadedmetadata', () => {
                console.log('视频元数据加载完成');
                this.updateVideoInfo();
                this.resizeCanvas();
                this.updateOverlay();
            });
            
            this.videoPlayer.addEventListener('canplay', () => {
                console.log('视频可以播放');
                this.resizeCanvas();
            });
            
            this.videoPlayer.addEventListener('error', (e) => {
                console.error('视频加载错误:', e);
                console.error('视频错误详情:', {
                    error: this.videoPlayer.error,
                    networkState: this.videoPlayer.networkState,
                    readyState: this.videoPlayer.readyState,
                    src: this.videoPlayer.src
                });
                
                // 显示错误信息给用户
                const videoInfo = document.getElementById('videoInfo');
                if (videoInfo) {
                    videoInfo.innerHTML = '<span style="color: red;">❌ 视频加载失败，请检查文件格式</span>';
                }
            });
        } else {
            console.error('没有找到上传的视频文件');
            console.log('尝试从文件输入元素获取视频文件...');
            
            // 备用方法：直接从文件输入元素获取
            const fileInput = document.getElementById('videoFileInput');
            if (fileInput && fileInput.files && fileInput.files[0]) {
                const file = fileInput.files[0];
                console.log('从文件输入获取到视频文件:', file.name);
                
                // 清理之前的URL
                if (this.videoPlayer.src && this.videoPlayer.src.startsWith('blob:')) {
                    URL.revokeObjectURL(this.videoPlayer.src);
                }
                
                try {
                    const videoUrl = URL.createObjectURL(file);
                    console.log('备用方法创建的视频URL:', videoUrl);
                    this.videoPlayer.src = videoUrl;
                } catch (error) {
                    console.error('备用方法创建视频URL失败:', error);
                    const videoInfo = document.getElementById('videoInfo');
                    if (videoInfo) {
                        videoInfo.innerHTML = '<span style="color: red;">❌ 备用方法无法创建视频URL</span>';
                    }
                }
                
                this.videoPlayer.addEventListener('loadedmetadata', () => {
                    console.log('视频元数据加载完成（备用方法）');
                    this.resizeCanvas();
                    this.updateOverlay();
                });
            } else {
                console.error('文件输入元素也没有视频文件');
            }
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

    updateVideoInfo() {
        if (!this.videoPlayer) return;
        
        const videoInfo = document.getElementById('videoInfo');
        const formatWarning = document.getElementById('formatWarning');
        
        if (videoInfo) {
            const width = this.videoPlayer.videoWidth;
            const height = this.videoPlayer.videoHeight;
            const duration = this.videoPlayer.duration;
            const currentFile = window.uploadModule ? window.uploadModule.getCurrentVideoFile() : null;
            
            let info = `视频尺寸: ${width} × ${height}`;
            if (duration && !isNaN(duration)) {
                info += ` | 时长: ${duration.toFixed(1)}秒`;
            }
            if (currentFile) {
                info += ` | 文件: ${currentFile.name} (${currentFile.type})`;
            }
            
            videoInfo.textContent = info;
            console.log('视频信息更新:', info);
            
            // 检查是否需要显示格式警告
            if (formatWarning && currentFile) {
                const fileName = currentFile.name.toLowerCase();
                const fileType = currentFile.type.toLowerCase();
                
                // 如果是MOV文件，显示格式警告
                if (fileName.endsWith('.mov') || fileType.includes('quicktime')) {
                    formatWarning.style.display = 'block';
                    console.log('显示MOV格式警告');
                } else {
                    formatWarning.style.display = 'none';
                }
            }
            
            // 如果视频加载失败，也显示格式警告
            if (formatWarning && this.videoPlayer.error) {
                formatWarning.style.display = 'block';
                console.log('视频加载失败，显示格式警告');
            }
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
