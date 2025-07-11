from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_from_directory
from app import db
from app.models import Platform, Livestream, Download, Setting
from app.utils import start_download, stop_download, get_download_status
import os
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    首页逻辑：展示监控中的直播间开播列表。
    1. 如果收藏的平台列表不为空，则从收藏的平台查找收藏的直播间在开播的地址信息。
    2. 否则从所有平台（不包含被屏蔽的平台）中取前5个平台，查找收藏的直播间是否存在开播。
    3. 同时查找下载管理中是否存在当前直播间的下载任务。
    """
    favorite_platforms = Platform.query.filter_by(is_favorite=True).all()

    livestreams_to_monitor = []

    if favorite_platforms:
        # 条件A: 从收藏的平台中，查找已收藏且在线的直播间
        livestreams_to_monitor = db.session.query(Livestream).join(Platform).filter(
            Platform.is_favorite == True,
            Livestream.is_favorite == True,
            Livestream.is_online == True
        ).all()
    else:
        # 条件B: 从未被屏蔽的前5个平台中，查找已收藏且在线的直播间
        platforms = Platform.query.filter_by(is_blocked=False).limit(5).all()
        if platforms:
            platform_ids = [p.platform_id for p in platforms]
            livestreams_to_monitor = Livestream.query.filter(
                Livestream.platform_id.in_(platform_ids),
                Livestream.is_favorite == True,
                Livestream.is_online == True
            ).all()

    display_data = []
    for stream in livestreams_to_monitor:
        # 查找当前直播间是否正在下载
        running_download = Download.query.filter_by(
            stream_id=stream.stream_id,
            status='running'
        ).first()

        task_status = "下载中" if running_download else "未下载"

        display_data.append({
            'stream': stream,
            'task_status': task_status,
            'download_id': running_download.id if running_download else None
        })

    return render_template('index.html', display_data=display_data)


@main_bp.route('/platforms')
def platforms():
    unblocked_platforms = Platform.query.filter_by(is_blocked=False).all()
    return render_template('platforms.html', platforms=unblocked_platforms)


@main_bp.route('/platforms/favorites')
def favorite_platforms():
    fav_platforms = Platform.query.filter_by(is_favorite=True).all()
    return render_template('favorite_platforms.html', platforms=fav_platforms)


@main_bp.route('/platforms/blocked')
def blocked_platforms():
    blk_platforms = Platform.query.filter_by(is_blocked=True).all()
    return render_template('blocked_platforms.html', platforms=blk_platforms)


@main_bp.route('/platform/<platform_id>')
def platform(platform_id):
    platform = Platform.query.filter_by(platform_id=platform_id).first_or_404()
    livestreams = Livestream.query.filter_by(platform_id=platform_id, is_blocked=False).all()
    favorite_streams = Livestream.query.filter_by(platform_id=platform_id, is_favorite=True).all()
    return render_template('platform.html', platform=platform, livestreams=livestreams,
                           favorite_streams=favorite_streams)


@main_bp.route('/player/<stream_id>')
def player(stream_id):
    stream = Livestream.query.filter_by(stream_id=stream_id).first_or_404()
    return render_template('player.html', stream=stream)


@main_bp.route('/livestream')
def livestream():
    favorite_streams = Livestream.query.filter_by(is_favorite=True).all()
    blocked_streams = Livestream.query.filter_by(is_blocked=True).all()
    return render_template('livestream.html', favorite_streams=favorite_streams, blocked_streams=blocked_streams)


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