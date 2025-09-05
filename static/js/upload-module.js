// 上传视频模块
class UploadModule {
    constructor() {
        this.currentVideoFile = null;
        this.init();
    }

    init() {
        this.render();
        // 延迟绑定事件，确保DOM元素已经创建
        setTimeout(() => {
            this.bindEvents();
        }, 100);
    }

    render() {
        console.log('渲染上传区域...');
        const uploadSection = document.getElementById('uploadSection');
        console.log('找到上传区域元素:', uploadSection);
        
        if (uploadSection) {
            uploadSection.innerHTML = `
                <div class="upload-section">
                    <h2>📁 上传高尔夫挥杆视频</h2>
                    <p>支持 MP4, MOV, AVI 等格式</p>
                    
                    <!-- 分辨率选择 -->
                    <div class="resolution-selector" style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 10px; border: 1px solid #e9ecef;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 16px;">🎯 分析分辨率选择</h3>
                        <p style="margin: 0 0 15px 0; color: #6c757d; font-size: 14px;">不同分辨率会影响检测精度和处理速度</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="320" style="margin-right: 8px;">
                                <span>320×320<br><small style="color: #6c757d;">快速 (80.2%)</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #28a745; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="480" checked style="margin-right: 8px;">
                                <span>480×480<br><small style="color: #28a745;">推荐 (80.9%)</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="640" style="margin-right: 8px;">
                                <span>640×640<br><small style="color: #6c757d;">标准 (77.9%)</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="800" style="margin-right: 8px;">
                                <span>800×800<br><small style="color: #6c757d;">高精度 (77.9%)</small></span>
                            </label>
                        </div>
                        <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 12px;">括号内为测试检测率，480×480为当前推荐设置</p>
                    </div>
                    
                    <!-- 高级参数调节 -->
                    <div class="advanced-params" style="margin: 20px 0; padding: 15px; background: #fff3cd; border-radius: 10px; border: 1px solid #ffeaa7;">
                        <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 16px;">⚙️ 高级检测参数调节</h3>
                        <p style="margin: 0 0 15px 0; color: #856404; font-size: 14px;">调节YOLOv8检测参数以优化检测效果</p>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <!-- 置信度阈值 -->
                            <div class="param-group">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #856404;">置信度阈值 (Confidence)</label>
                                <input type="range" id="confidenceSlider" min="0.001" max="0.1" step="0.001" value="0.01" 
                                       style="width: 100%; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #856404;">
                                    <span>0.001</span>
                                    <span id="confidenceValue">0.01</span>
                                    <span>0.1</span>
                                </div>
                                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">
                                    越低检测越多，但可能增加误检。推荐: 0.01
                                </p>
                            </div>
                            
                            <!-- IoU阈值 -->
                            <div class="param-group">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #856404;">IoU阈值 (NMS)</label>
                                <input type="range" id="iouSlider" min="0.1" max="0.9" step="0.1" value="0.7" 
                                       style="width: 100%; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #856404;">
                                    <span>0.1</span>
                                    <span id="iouValue">0.7</span>
                                    <span>0.9</span>
                                </div>
                                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">
                                    控制重复检测框过滤。推荐: 0.7
                                </p>
                            </div>
                            
                            <!-- 最大检测数量 -->
                            <div class="param-group">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #856404;">最大检测数量</label>
                                <input type="range" id="maxDetSlider" min="1" max="50" step="1" value="10" 
                                       style="width: 100%; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #856404;">
                                    <span>1</span>
                                    <span id="maxDetValue">10</span>
                                    <span>50</span>
                                </div>
                                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">
                                    每帧最大检测目标数。推荐: 10
                                </p>
                            </div>
                        </div>
                        
                        <!-- 参数说明 -->
                        <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 8px; border: 1px solid #b3d9ff;">
                            <h4 style="margin: 0 0 8px 0; color: #004085; font-size: 14px;">📖 参数说明</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #004085; font-size: 12px; line-height: 1.4;">
                                <li><strong>置信度阈值</strong>: 检测框的最小置信度，越低检测越多但可能误检</li>
                                <li><strong>IoU阈值</strong>: 非极大值抑制阈值，用于过滤重叠的检测框</li>
                                <li><strong>最大检测数量</strong>: 每帧最多保留的检测框数量</li>
                                <li><strong>当前推荐设置</strong>: 置信度0.01 + IoU0.7 + 最大检测10个</li>
                            </ul>
                        </div>
                    </div>
                    
                    <input type="file" id="videoFileInput" class="file-input" accept="video/*">
                    <button class="upload-btn" onclick="document.getElementById('videoFileInput').click()">
                        选择视频文件
                    </button>
                    <div id="uploadStatus" class="status" style="display: none;"></div>
                </div>
            `;
            console.log('上传区域HTML已设置');
            
            // 添加滑块交互逻辑
            this.setupParameterSliders();
        } else {
            console.error('找不到上传区域元素!');
        }
    }

    setupParameterSliders() {
        // 置信度滑块
        const confidenceSlider = document.getElementById('confidenceSlider');
        const confidenceValue = document.getElementById('confidenceValue');
        if (confidenceSlider && confidenceValue) {
            confidenceSlider.addEventListener('input', (e) => {
                confidenceValue.textContent = parseFloat(e.target.value).toFixed(3);
            });
        }
        
        // IoU滑块
        const iouSlider = document.getElementById('iouSlider');
        const iouValue = document.getElementById('iouValue');
        if (iouSlider && iouValue) {
            iouSlider.addEventListener('input', (e) => {
                iouValue.textContent = parseFloat(e.target.value).toFixed(1);
            });
        }
        
        // 最大检测数量滑块
        const maxDetSlider = document.getElementById('maxDetSlider');
        const maxDetValue = document.getElementById('maxDetValue');
        if (maxDetSlider && maxDetValue) {
            maxDetSlider.addEventListener('input', (e) => {
                maxDetValue.textContent = e.target.value;
            });
        }
    }

    bindEvents() {
        console.log('绑定事件...');
        const videoFileInput = document.getElementById('videoFileInput');
        console.log('找到文件输入元素:', videoFileInput);
        
        if (videoFileInput) {
            videoFileInput.addEventListener('change', (event) => {
                console.log('文件选择事件触发!');
                this.handleFileSelect(event);
            });
            console.log('change事件监听器已添加');
        } else {
            console.error('找不到文件输入元素!');
        }
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        console.log('文件已选择:', file.name, file.size, file.type);
        this.currentVideoFile = file;
        this.showStatus('正在分析视频...', 'processing');

        try {
            const formData = new FormData();
            formData.append('video', file);
            
            // 获取选择的分辨率
            const resolutionInput = document.querySelector('input[name="resolution"]:checked');
            const resolution = resolutionInput ? resolutionInput.value : '480';
            formData.append('resolution', resolution);
            
            // 获取高级参数
            const confidence = document.getElementById('confidenceSlider')?.value || '0.01';
            const iou = document.getElementById('iouSlider')?.value || '0.7';
            const maxDet = document.getElementById('maxDetSlider')?.value || '10';
            
            formData.append('confidence', confidence);
            formData.append('iou', iou);
            formData.append('max_det', maxDet);
            
            console.log('FormData已创建，准备发送请求到 /analyze/video');
            console.log('参数:', { resolution, confidence, iou, maxDet });

            const response = await fetch('/analyze/video', {
                method: 'POST',
                body: formData
            });

            console.log('收到响应:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const resp = await response.json();
            console.log('解析响应结果:', resp);

            // 后台任务模式：返回 job_id 后轮询
            if (resp && resp.job_id) {
                const jobId = resp.job_id;
                this.showStatus('已提交，正在后台处理中…', 'processing');
                const data = await this.pollJob(jobId);
                this.showStatus('分析完成！', 'success');
                this.onAnalysisComplete(data);
            } else {
                // 兼容旧同步模式
                this.showStatus('分析完成！', 'success');
                this.onAnalysisComplete(resp);
            }
            
        } catch (error) {
            console.error('上传失败:', error);
            this.showStatus(`分析失败: ${error.message}`, 'error');
        }
    }

    async pollJob(jobId) {
        // 简单轮询：每2秒查一次，最大等待15分钟
        const maxTries = 450; // 2s * 450 ≈ 900s
        for (let i = 0; i < maxTries; i++) {
            try {
                const r = await fetch(`/analyze/video/status?job_id=${jobId}`);
                if (!r.ok) throw new Error(`status ${r.status}`);
                const j = await r.json();
                if (j.status === 'done') {
                    // 将 job_id 一并返回，便于其他模块后续继续查询补充字段
                    return Object.assign({ job_id: j.job_id }, j.result || {});
                }
                if (j.status === 'error') throw new Error(j.error || '后台任务失败');
                this.showStatus(`后台处理中… 进度: ${j.progress || 0} 帧`, 'processing');
            } catch (e) {
                console.warn('轮询失败，重试中', e);
            }
            await new Promise(res => setTimeout(res, 2000));
        }
        throw new Error('等待超时');
    }

    showStatus(message, type) {
        const statusDiv = document.getElementById('uploadStatus');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
        }
    }

    onAnalysisComplete(data) {
        console.log('分析完成，触发事件:', data);
        console.log('swing_phases数据:', data.swing_phases);
        console.log('swing_phases类型:', typeof data.swing_phases);
        console.log('swing_phases长度:', data.swing_phases ? data.swing_phases.length : 'null/undefined');
        
        // 触发自定义事件，通知其他模块
        const event = new CustomEvent('analysisComplete', {
            detail: data
        });
        document.dispatchEvent(event);
        
        console.log('事件已触发');
    }

    getCurrentVideoFile() {
        return this.currentVideoFile;
    }
}

// 创建全局实例
window.uploadModule = new UploadModule();
console.log('✅ uploadModule 已创建并加载到全局作用域');
