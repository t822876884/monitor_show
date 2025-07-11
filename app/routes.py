from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_from_directory
from app import db
from app.models import Platform, Livestream, Download, Setting
from app.utils import start_download, stop_download, get_download_status
import os
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    platforms = Platform.query.filter_by(is_blocked=False).all()
    favorite_platforms = Platform.query.filter_by(is_favorite=True).all()
    return render_template('index.html', platforms=platforms, favorite_platforms=favorite_platforms)

@main_bp.route('/platform/<platform_id>')
def platform(platform_id):
    platform = Platform.query.filter_by(platform_id=platform_id).first_or_404()
    livestreams = Livestream.query.filter_by(platform_id=platform_id, is_blocked=False).all()
    favorite_streams = Livestream.query.filter_by(platform_id=platform_id, is_favorite=True).all()
    return render_template('platform.html', platform=platform, livestreams=livestreams, favorite_streams=favorite_streams)

@main_bp.route('/player/<stream_id>')
def player(stream_id):
    stream = Livestream.query.filter_by(stream_id=stream_id).first_or_404()
    return render_template('player.html', stream=stream)

@main_bp.route('/settings')
def settings():
    settings = Setting.query.all()
    return render_template('settings.html', settings=settings)

@main_bp.route('/settings/update', methods=['POST'])
def update_settings():
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            setting = Setting.query.filter_by(key=setting_key).first()
            if setting:
                setting.value = value
    
    db.session.commit()
    return redirect(url_for('main.settings'))

@main_bp.route('/api/toggle_favorite/<type>/<id>')
def toggle_favorite(type, id):
    if type == 'platform':
        item = Platform.query.filter_by(platform_id=id).first_or_404()
    else:  # livestream
        item = Livestream.query.filter_by(stream_id=id).first_or_404()
    
    item.is_favorite = not item.is_favorite
    db.session.commit()
    
    return jsonify({'success': True, 'is_favorite': item.is_favorite})

@main_bp.route('/api/toggle_block/<type>/<id>')
def toggle_block(type, id):
    if type == 'platform':
        item = Platform.query.filter_by(platform_id=id).first_or_404()
    else:  # livestream
        item = Livestream.query.filter_by(stream_id=id).first_or_404()
    
    item.is_blocked = not item.is_blocked
    db.session.commit()
    
    return jsonify({'success': True, 'is_blocked': item.is_blocked})

@main_bp.route('/api/start_download/<stream_id>')
def api_start_download(stream_id):
    stream = Livestream.query.filter_by(stream_id=stream_id).first_or_404()
    download_path = Setting.query.filter_by(key='download_path').first().value
    ffmpeg_path = Setting.query.filter_by(key='ffmpeg_path').first().value
    
    # 创建下载记录
    filename = f"{stream.platform_id}_{stream.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.flv"
    filepath = os.path.join(download_path, filename)
    
    download = Download(
        stream_id=stream_id,
        filename=filename,
        filepath=filepath,
        status='pending',
        start_time=datetime.now()
    )
    
    db.session.add(download)
    db.session.commit()
    
    # 启动下载
    success = start_download(download.id, stream.address, filepath, ffmpeg_path)
    
    if not success:
        download.status = 'failed'
        db.session.commit()
        return jsonify({'success': False, 'message': '启动下载失败'})
    
    return jsonify({'success': True, 'download_id': download.id})

@main_bp.route('/api/stop_download/<download_id>')
def api_stop_download(download_id):
    download = Download.query.get_or_404(download_id)
    success = stop_download(download_id)
    
    if success:
        download.status = 'stopped'
        download.end_time = datetime.now()
        db.session.commit()
    
    return jsonify({'success': success})

@main_bp.route('/downloads')
def downloads():
    downloads = Download.query.order_by(Download.start_time.desc()).all()
    return render_template('downloads.html', downloads=downloads)

@main_bp.route('/download/<filename>')
def download_file(filename):
    download_path = Setting.query.filter_by(key='download_path').first().value
    return send_from_directory(download_path, filename, as_attachment=True)