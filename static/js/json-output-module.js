// JSON输出模块
class JsonOutputModule {
    constructor() {
        this.currentAnalysisData = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.render();
    }

    render() {
        // 等待视频播放器创建后再渲染
        this.waitForVideoPlayer();
    }
    
    waitForVideoPlayer() {
        const checkInterval = setInterval(() => {
            const videoSection = document.querySelector('.video-container');
            if (videoSection && !document.querySelector('.json-output-section')) {
                clearInterval(checkInterval);
                console.log('找到视频播放器区域，创建JSON输出区域');
                // 等待一小段时间确保视频播放器完全渲染
                setTimeout(() => {
                    this.createJsonSection();
                }, 200);
            }
        }, 100);
    }
    
    createJsonSection() {
        const videoSection = document.querySelector('.video-container');
        if (videoSection && !document.querySelector('.json-output-section')) {
            const jsonSection = document.createElement('div');
            jsonSection.className = 'result-card json-output-section';
            jsonSection.innerHTML = `
                <h3>📄 Golftrainer兼容JSON输出</h3>
                <div class="json-controls">
                    <button id="previewJsonBtn" class="btn btn-primary">预览JSON</button>
                    <button id="downloadJsonBtn" class="btn btn-secondary">下载JSON文件</button>
                    <button id="copyJsonBtn" class="btn btn-secondary">复制到剪贴板</button>
                </div>
                <div class="json-preview" id="jsonPreview" style="display: none;">
                    <h4>JSON预览</h4>
                    <div class="json-content">
                        <pre id="jsonContent"></pre>
                    </div>
                </div>
            `;
            videoSection.parentNode.appendChild(jsonSection);
            console.log('JSON输出区域创建完成');
            
            // 绑定按钮事件
            this.bindJsonControls();
        }
    }

    bindEvents() {
        // 监听结果更新事件
        document.addEventListener('resultsUpdated', (event) => {
            console.log('JSON输出模块收到resultsUpdated事件');
            // 等待DOM元素创建完成后再显示JSON输出
            setTimeout(() => {
                this.displayJsonOutput(event.detail);
            }, 800);
        });
    }

    displayJsonOutput(data) {
        this.currentAnalysisData = data;
        console.log('JSON输出模块收到数据:', data);
        
        // 等待JSON区域创建完成
        setTimeout(() => {
            this.updateJsonContent(data);
        }, 100);
    }

    updateJsonContent(data) {
        const jsonPreview = document.getElementById('jsonPreview');
        const jsonContent = document.getElementById('jsonContent');
        
        console.log('查找JSON元素:', {
            jsonPreview: jsonPreview,
            jsonContent: jsonContent
        });
        
        if (jsonPreview && jsonContent) {
            const golftrainerJson = this.generateGolftrainerJson(data);
            console.log('生成的Golftrainer JSON:', golftrainerJson);
            
            jsonContent.textContent = JSON.stringify(golftrainerJson, null, 2);
            
            // 自动显示JSON预览
            jsonPreview.style.display = 'block';
            
            // 更新预览按钮状态
            const previewJsonBtn = document.getElementById('previewJsonBtn');
            if (previewJsonBtn) {
                previewJsonBtn.textContent = '隐藏JSON';
                previewJsonBtn.className = 'btn btn-secondary';
            }
        } else {
            console.error('JSON元素未找到，等待DOM创建...');
            // 如果元素还没创建，等待一下再试，最多重试5次
            if (!this._retryCount) this._retryCount = 0;
            if (this._retryCount < 5) {
                this._retryCount++;
                setTimeout(() => this.updateJsonContent(data), 500);
            } else {
                console.error('JSON元素创建失败，已达到最大重试次数');
                this._retryCount = 0; // 重置计数器
            }
        }
    }

    bindJsonControls() {
        const previewJsonBtn = document.getElementById('previewJsonBtn');
        const downloadJsonBtn = document.getElementById('downloadJsonBtn');
        const copyJsonBtn = document.getElementById('copyJsonBtn');

        if (previewJsonBtn) {
            previewJsonBtn.addEventListener('click', () => {
                this.toggleJsonPreview();
            });
        }

        if (downloadJsonBtn) {
            downloadJsonBtn.addEventListener('click', () => {
                this.downloadJson();
            });
        }

        if (copyJsonBtn) {
            copyJsonBtn.addEventListener('click', () => {
                this.copyToClipboard();
            });
        }
    }

    toggleJsonPreview() {
        const jsonPreview = document.getElementById('jsonPreview');
        const previewJsonBtn = document.getElementById('previewJsonBtn');
        
        if (jsonPreview && previewJsonBtn) {
            if (jsonPreview.style.display === 'none') {
                jsonPreview.style.display = 'block';
                previewJsonBtn.textContent = '隐藏JSON';
                previewJsonBtn.className = 'btn btn-secondary';
            } else {
                jsonPreview.style.display = 'none';
                previewJsonBtn.textContent = '预览JSON';
                previewJsonBtn.className = 'btn btn-primary';
            }
        }
    }

    downloadJson() {
        if (!this.currentAnalysisData) return;
        
        const golftrainerJson = this.generateGolftrainerJson(this.currentAnalysisData);
        const jsonString = JSON.stringify(golftrainerJson, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'golftrainer_analysis.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    copyToClipboard() {
        if (!this.currentAnalysisData) return;
        
        const golftrainerJson = this.generateGolftrainerJson(this.currentAnalysisData);
        const jsonString = JSON.stringify(golftrainerJson, null, 2);
        
        navigator.clipboard.writeText(jsonString).then(() => {
            // 显示复制成功提示
            const copyBtn = document.getElementById('copyJsonBtn');
            if (copyBtn) {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✅ 已复制';
                copyBtn.className = 'btn btn-success';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.className = 'btn btn-secondary';
                }, 2000);
            }
        }).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        });
    }

    generateGolftrainerJson(data) {
        return {
            version: 1.0,
            video_spec: {
                height: data.video_info?.height || 1080,
                width: data.video_info?.width || 1920,
                num_frames: data.total_frames || 0,
                fps: data.video_info?.fps || 30,
                scale: 100,
                rotate: ""
            },
            video_input: {
                fname: "uploaded_video.mp4",
                size: 0
            },
            num_frames: data.total_frames || 0,
            pose_result: {
                poses: [],
                handed: "RightHanded",
                poses_count: 1
            },
            club_head_result: {
                norm_points: data.club_head_trajectory || [],
                algos: ["YOLOv8_Detection"] * (data.total_frames || 0),
                quality_scores: [],
                trajectory_stats: {
                    total_points: data.detected_frames || 0,
                    detection_rate: data.detection_rate || 0,
                    avg_confidence: data.avg_confidence || 0
                }
            },
            mp_result: {
                landmarks: [],
                norm_points: []
            },
            swing_analysis: {
                phases: {},
                key_frames: {},
                summary: {}
            }
        };
    }
}

// 创建全局实例
window.jsonOutputModule = new JsonOutputModule();
console.log('✅ jsonOutputModule 已创建并加载到全局作用域');
