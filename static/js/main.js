// 主控制模块
class MainController {
    constructor() {
        this.init();
    }

    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }

    onDOMReady() {
        console.log('GolfTracker 模块化系统初始化完成');
        
        // 检查所有模块是否正确加载
        this.checkModules();
        
        // 设置全局错误处理
        this.setupErrorHandling();
    }

    checkModules() {
        const requiredModules = [
            'uploadModule',
            'resultsModule', 
            'trajectoryModule',
            'videoPlayerModule',
            'jsonOutputModule',
            'frameAnalysisModule',
            'swingVisualizationModule'
        ];
        
        console.log('检查模块加载状态...');
        
        requiredModules.forEach(module => {
            const exists = !!window[module];
            console.log(`模块 ${module}: ${exists ? '✅ 已加载' : '❌ 未加载'}`);
            if (exists) {
                console.log(`  - 类型: ${typeof window[module]}`);
                console.log(`  - 构造函数: ${window[module].constructor.name}`);
            }
        });
        
        const missingModules = requiredModules.filter(module => !window[module]);
        
        if (missingModules.length > 0) {
            console.error('缺少模块:', missingModules);
        } else {
            console.log('所有模块加载成功');
        }
    }

    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('全局错误:', event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('未处理的Promise拒绝:', event.reason);
        });
    }
}

// 创建主控制器实例
window.mainController = new MainController();
