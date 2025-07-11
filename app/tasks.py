import threading
import time
from datetime import datetime, timedelta
from app import db
from app.models import Platform, Livestream, Setting
from app.data_fetcher import DataFetcher

def update_platforms(app):
    """更新平台列表"""
    with app.app_context():
        api_url = Setting.query.filter_by(key='api_url').first().value
        fetcher = DataFetcher(api_url)
        return fetcher.fetch_platforms()

def update_livestreams(app):
    """更新所有平台的直播间列表"""
    with app.app_context():
        platforms = Platform.query.filter_by(is_blocked=False).all()
        for platform in platforms:
            fetcher = DataFetcher(None)  # API URL在fetch_livestreams中指定
            fetcher.fetch_livestreams(platform.platform_id, platform.address)

def check_livestream_status(app):
    """检查直播间状态，将长时间未更新的直播间标记为离线"""
    with app.app_context():
        # 获取检查间隔时间
        check_interval = int(Setting.query.filter_by(key='check_interval').first().value)
        # 计算超时时间
        timeout = datetime.now() - timedelta(seconds=check_interval*2)
        
        # 查找超时的直播间
        offline_streams = Livestream.query.filter(
            Livestream.is_online == True,
            Livestream.last_check < timeout
        ).all()
        
        # 标记为离线
        for stream in offline_streams:
            stream.is_online = False
        
        db.session.commit()

def background_task(app):
    """后台任务主函数"""
    while True:
        try:
            # 更新平台列表
            update_platforms(app)
            # 更新直播间列表
            update_livestreams(app)
            # 检查直播间状态
            check_livestream_status(app)
            
            # 获取检查间隔时间
            with app.app_context():
                check_interval = int(Setting.query.filter_by(key='check_interval').first().value)
            
            # 等待下一次检查
            time.sleep(check_interval)
        except Exception as e:
            print(f"Background task error: {e}")
            time.sleep(60)  # 出错后等待1分钟再重试

def start_background_tasks():
    """启动后台任务线程"""
    from app import create_app
    app = create_app()
    
    thread = threading.Thread(target=background_task, args=(app,))
    thread.daemon = True
    thread.start()
    
    return thread