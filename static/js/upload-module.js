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
            // 页面加载时就加载策略选项
            this.loadAvailableStrategies();
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
                        <p style="margin: 0 0 15px 0; color: #6c757d; font-size: 14px;">系统会根据视频实际尺寸自动选择最佳分辨率，或手动指定</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px;">
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="960" style="margin-right: 8px;">
                                <span>960×960<br><small style="color: #6c757d;">平衡模式</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="auto" style="margin-right: 8px;">
                                <span>自动<br><small style="color: #6c757d;">根据视频尺寸</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="640" style="margin-right: 8px;">
                                <span>640×640<br><small style="color: #6c757d;">中等精度</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="480" style="margin-right: 8px;">
                                <span>480×480<br><small style="color: #6c757d;">快速模式</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="1280" style="margin-right: 8px;">
                                <span>1280×1280<br><small style="color: #6c757d;">高精度</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="1600" style="margin-right: 8px;">
                                <span>1600×1600<br><small style="color: #6c757d;">超高精度</small></span>
                            </label>
                            <label style="display: flex; align-items: center; padding: 8px 12px; background: white; border: 2px solid #28a745; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="resolution" value="1920" checked style="margin-right: 8px;">
                                <span>1920×1920<br><small style="color: #28a745;">最高精度 (默认)</small></span>
                            </label>
                        </div>
                        <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 12px;">
                            <strong>默认1920×1920</strong>：最高精度检测模式 | <strong>自动模式</strong>：根据视频尺寸动态调整
                        </p>
                    </div>
                    
                    <!-- 优化策略选择 -->
                    <div class="strategy-selector" style="margin: 20px 0; padding: 15px; background: #e8f5e8; border-radius: 10px; border: 1px solid #c3e6c3;">
                        <h3 style="margin: 0 0 10px 0; color: #2d5a2d; font-size: 16px;">🎯 轨迹优化策略选择</h3>
                        <p style="margin: 0 0 15px 0; color: #2d5a2d; font-size: 14px;">选择轨迹优化算法来改善检测结果</p>
                        
                        <div class="strategy-options" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                            <label style="display: flex; align-items: center; padding: 10px 12px; background: white; border: 2px solid #28a745; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                                <input type="radio" name="optimizationStrategy" value="auto_fill" checked style="margin-right: 8px;">
                                <div>
                                    <div style="font-weight: 600; color: #2d5a2d;">自动补齐算法</div>
                                    <small style="color: #6c757d;">将未检测到的帧自动补齐到最近有效帧位置</small>
                                </div>
                            </label>
                        </div>
                        
                        <div id="strategyDescription" class="strategy-description" style="margin-top: 10px; padding: 8px 12px; background: #f8f9fa; border-radius: 4px; font-size: 12px; color: #6c757d; line-height: 1.4; min-height: 20px;">
                            自动补齐算法：智能填充未检测帧，提高轨迹连续性
                        </div>
                    </div>
                    
                    <!-- 高级参数调节 -->
                    <div class="advanced-params" style="margin: 20px 0; padding: 15px; background: #fff3cd; border-radius: 10px; border: 1px solid #ffeaa7;">
                        <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 16px;">⚙️ 高级检测参数调节</h3>
                        <p style="margin: 0 0 15px 0; color: #856404; font-size: 14px;">调节YOLOv8检测参数以优化检测效果</p>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <!-- 置信度阈值 -->
                            <div class="param-group">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #856404;">置信度阈值 (Confidence)</label>
                                <input type="range" id="confidenceSlider" min="0.001" max="0.1" step="0.001" value="0.2" 
                                       style="width: 100%; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #856404;">
                                    <span>0.001</span>
                                    <span id="confidenceValue">0.2</span>
                                    <span>0.1</span>
                                </div>
                                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">
                                    <strong>当前: 0.2 (20%)</strong> - 高精度设置，减少误检
                                </p>
                            </div>
                            
                            <!-- IoU阈值 -->
                            <div class="param-group">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #856404;">IoU阈值 (NMS)</label>
                                <input type="range" id="iouSlider" min="0.1" max="0.9" step="0.1" value="0.9" 
                                       style="width: 100%; margin-bottom: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #856404;">
                                    <span>0.1</span>
                                    <span id="iouValue">0.9</span>
                                    <span>0.9</span>
                                </div>
                                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">
                                    <strong>当前: 0.9 (90%)</strong> - 严格去重阈值，高精度检测
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
                                    <strong>当前: 10</strong> - 每帧最大检测目标数，适合高尔夫场景
                                </p>
                            </div>
                        </div>
                        
                        <!-- 参数说明 -->
                        <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 8px; border: 1px solid #b3d9ff;">
                            <h4 style="margin: 0 0 8px 0; color: #004085; font-size: 14px;">📖 参数说明</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #004085; font-size: 12px; line-height: 1.4;">
                                <li><strong>置信度阈值 (0.2)</strong>: 高精度设置，减少误检，提高检测质量</li>
                                <li><strong>IoU阈值 (0.9)</strong>: 严格去重设置，过滤90%以上重叠的检测框</li>
                                <li><strong>最大检测数量 (10)</strong>: 每帧最多保留10个检测结果，适合高尔夫场景</li>
                                <li><strong>动态分辨率</strong>: 系统根据视频实际尺寸自动选择最佳分析分辨率</li>
                            </ul>
                        </div>
                    </div>
                    
                    <input type="file" id="videoFileInput" class="file-input" accept="video/*">
                    <button class="upload-btn" onclick="document.getElementById('videoFileInput').click()">
                        选择视频文件
                    </button>
                    
                    <!-- 开始分析按钮 -->
                    <div id="startAnalysisSection" style="display: none; margin-top: 20px;">
                        <button id="startAnalysisBtn" class="upload-btn" style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 12px 30px; font-size: 16px; font-weight: 600; border: none; border-radius: 25px; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);">
                            🚀 开始分析视频
                        </button>
                        <p style="margin-top: 10px; color: #6c757d; font-size: 14px;">
                            已选择视频文件，请确认参数设置后点击开始分析
                        </p>
                    </div>
                    
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
        
        // 显示开始分析按钮
        const startAnalysisSection = document.getElementById('startAnalysisSection');
        if (startAnalysisSection) {
            startAnalysisSection.style.display = 'block';
        }
        
        this.showStatus('视频已选择，请确认参数后点击开始分析', 'info');
    }

    async loadAvailableStrategies() {
        try {
            console.log('🔄 开始加载策略...');
            const response = await fetch('/analyze/strategies');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            this.availableStrategies = data.strategies || {};
            console.log('✅ 策略加载成功:', this.availableStrategies);
            
            // 更新策略选项
            this.updateStrategyOptions();
            
            // 绑定策略选择事件
            this.bindStrategyEvents();
            
        } catch (error) {
            console.error('❌ 加载策略失败:', error);
            this.availableStrategies = {};
        }
    }

    updateStrategyOptions() {
        const strategyOptions = document.querySelector('.strategy-options');
        if (!strategyOptions) {
            console.error('❌ 找不到策略选项容器');
            return;
        }
        
        console.log('🔄 更新策略选项...');
        console.log('可用策略:', this.availableStrategies);
        
        // 清空现有选项
        strategyOptions.innerHTML = '';
        
        // 不再添加原始检测选项，只使用自动补齐算法
        
        // 确保始终显示自动补齐算法选项，无论API是否成功
        const autoFillStrategy = this.availableStrategies?.auto_fill || {
            name: "自动补齐算法",
            description: "将未检测到的帧自动补齐到最近有效帧位置，提高轨迹连续性"
        };
        
        const label = document.createElement('label');
        label.style.cssText = 'display: flex; align-items: center; padding: 10px 12px; background: white; border: 2px solid #28a745; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;';
        
        label.innerHTML = `
            <input type="radio" name="optimizationStrategy" value="auto_fill" checked style="margin-right: 8px;">
            <div>
                <div style="font-weight: 600; color: #2d5a2d;">${autoFillStrategy.name}</div>
                <small style="color: #6c757d;">${autoFillStrategy.description}</small>
            </div>
        `;
        
        strategyOptions.appendChild(label);
        console.log(`✅ 添加策略选项: auto_fill - ${autoFillStrategy.name}`);
    }

    bindStrategyEvents() {
        // 绑定策略选择事件
        const strategyInputs = document.querySelectorAll('input[name="optimizationStrategy"]');
        strategyInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateStrategyDescription();
            });
        });
        
        // 绑定开始分析按钮事件
        const startAnalysisBtn = document.getElementById('startAnalysisBtn');
        if (startAnalysisBtn) {
            startAnalysisBtn.addEventListener('click', () => {
                this.startAnalysis();
            });
        }
    }

    updateStrategyDescription() {
        const selectedStrategy = document.querySelector('input[name="optimizationStrategy"]:checked');
        const descriptionDiv = document.getElementById('strategyDescription');
        
        if (!selectedStrategy || !descriptionDiv) return;
        
        if (this.availableStrategies && this.availableStrategies[selectedStrategy.value]) {
            const strategy = this.availableStrategies[selectedStrategy.value];
            descriptionDiv.textContent = `${strategy.name}: ${strategy.description}`;
        } else {
            descriptionDiv.textContent = '自动补齐算法：智能填充未检测帧，提高轨迹连续性';
        }
    }

    async startAnalysis() {
        if (!this.currentVideoFile) {
            this.showStatus('请先选择视频文件', 'error');
            return;
        }

        this.showStatus('正在分析视频...', 'processing');
        
        // 隐藏开始分析按钮
        const startAnalysisSection = document.getElementById('startAnalysisSection');
        if (startAnalysisSection) {
            startAnalysisSection.style.display = 'none';
        }

        try {
            const formData = new FormData();
            formData.append('video', this.currentVideoFile);
            
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
            
            // 获取选择的优化策略
            const strategyInput = document.querySelector('input[name="optimizationStrategy"]:checked');
            const selectedStrategy = strategyInput ? strategyInput.value : 'original';
            formData.append('optimization_strategy', selectedStrategy);
            
            console.log('FormData已创建，准备发送请求到 /analyze/video');
            console.log('参数:', { resolution, confidence, iou, maxDet, selectedStrategy });

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
            console.error('分析失败:', error);
            this.showStatus(`分析失败: ${error.message}`, 'error');
            
            // 重新显示开始分析按钮
            if (startAnalysisSection) {
                startAnalysisSection.style.display = 'block';
            }
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
