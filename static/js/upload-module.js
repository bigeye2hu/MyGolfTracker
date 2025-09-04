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
                    <input type="file" id="videoFileInput" class="file-input" accept="video/*">
                    <button class="upload-btn" onclick="document.getElementById('videoFileInput').click()">
                        选择视频文件
                    </button>
                    <div id="uploadStatus" class="status" style="display: none;"></div>
                </div>
            `;
            console.log('上传区域HTML已设置');
        } else {
            console.error('找不到上传区域元素!');
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
            console.log('FormData已创建，准备发送请求到 /analyze/video');

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
