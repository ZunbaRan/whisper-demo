// 自定义 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('RSS 音频处理系统已加载');
    
    // 添加页面加载动画
    const pageContent = document.querySelector('.content');
    if (pageContent) {
        pageContent.style.opacity = '0';
        setTimeout(() => {
            pageContent.style.transition = 'opacity 0.5s ease';
            pageContent.style.opacity = '1';
        }, 100);
    }
});

// 通用的 API 调用函数
async function callApi(url, method = 'GET', body = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url);
        
        // 检查响应状态
        if (!response.ok) {
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || `HTTP error! status: ${response.status}`;
            } catch (e) {
                errorMessage = `HTTP error! status: ${response.status}`;
            }
            throw new Error(errorMessage);
        }

        // 尝试解析 JSON 响应
        try {
            return await response.json();
        } catch (e) {
            // 如果响应不是 JSON 格式，返回原始文本
            return await response.text();
        }
    } catch (error) {
        console.error('API 调用失败:', error);
        throw error;
    }
}

// 显示加载状态的函数
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>';
    }
}

// 显示错误信息的函数
function showError(elementId, error) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="alert alert-danger" role="alert">加载失败: ${error.message}</div>`;
    }
}

// 初始化工具提示
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 