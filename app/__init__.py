from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import os
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # 添加上下文处理器，为所有模板提供now变量
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    with app.app_context():
        db.create_all()
        # 初始化设置
        from app.models import Setting
        if not Setting.query.filter_by(key='api_url').first():
            default_settings = [
                Setting(key='api_url', value='http://api.hclyz.com:81/mf/json.txt', description='API基础URL'),
                Setting(key='download_path', value=os.path.join(os.path.dirname(app.instance_path), 'downloads'), description='下载保存路径'),
                Setting(key='check_interval', value='300', description='检查直播间状态间隔(秒)'),
                Setting(key='ffmpeg_path', value='ffmpeg', description='FFmpeg可执行文件路径')
            ]
            db.session.add_all(default_settings)
            db.session.commit()
            
            # 创建下载目录
            os.makedirs(default_settings[1].value, exist_ok=True)
    
    return app