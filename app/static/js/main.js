$(document).ready(function() {
    // 切换收藏状态
    $('.toggle-favorite').click(function() {
        const type = $(this).data('type');
        const id = $(this).data('id');
        const btn = $(this);
        const icon = btn.find('i');
        
        $.getJSON(`/api/toggle_favorite/${type}/${id}`, function(data) {
            if (data.success) {
                if (data.is_favorite) {
                    icon.removeClass('bi-star').addClass('bi-star-fill');
                } else {
                    icon.removeClass('bi-star-fill').addClass('bi-star');
                }
                btn.data('status', data.is_favorite ? 1 : 0);
            }
        });
    });
    
    // 切换屏蔽状态
    $('.toggle-block').click(function() {
        const type = $(this).data('type');
        const id = $(this).data('id');
        const btn = $(this);
        const icon = btn.find('i');
        
        if (confirm(`确定要${btn.data('status') == 1 ? '取消' : '屏蔽'}此${type == 'platform' ? '平台' : '直播间'}吗？`)) {
            $.getJSON(`/api/toggle_block/${type}/${id}`, function(data) {
                if (data.success) {
                    if (data.is_blocked) {
                        icon.removeClass('bi-x-circle').addClass('bi-x-circle-fill');
                    } else {
                        icon.removeClass('bi-x-circle-fill').addClass('bi-x-circle');
                    }
                    btn.data('status', data.is_blocked ? 1 : 0);
                    
                    // 如果是在列表页面，可能需要刷新
                    if (type == 'platform' && window.location.pathname == '/') {
                        setTimeout(function() {
                            location.reload();
                        }, 500);
                    } else if (type == 'livestream' && window.location.pathname.includes('/platform/')) {
                        setTimeout(function() {
                            location.reload();
                        }, 500);
                    }
                }
            });
        }
    });
});