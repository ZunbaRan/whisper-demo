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