import subprocess
import os
import signal
import psutil
from threading import Thread
from app import db
from app.models import Download
from datetime import datetime
import time

# 存储下载进程
download_processes = {}

def start_download(download_id, stream_url, output_path, ffmpeg_path):
    """启动下载进程"""
    try:
        # 构建FFmpeg命令
        command = [
            ffmpeg_path,
            '-i', stream_url,
            '-c', 'copy',  # 不重新编码，直接复制流
            '-f', 'flv',
            output_path
        ]
        
        # 启动进程
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 存储进程信息
        download_processes[str(download_id)] = {
            'process': process,
            'pid': process.pid,
            'start_time': datetime.now()
        }
        
        # 启动监控线程
        monitor_thread = Thread(target=monitor_download, args=(download_id, process))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return True
    except Exception as e:
        print(f"Error starting download: {e}")
        return False

def stop_download(download_id):
    """停止下载进程"""
    download_id = str(download_id)
    if download_id in download_processes:
        try:
            process_info = download_processes[download_id]
            process = process_info['process']
            
            # 尝试终止进程
            if process.poll() is None:  # 进程仍在运行
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix/Linux/Mac
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # 从字典中移除
            del download_processes[download_id]
            return True
        except Exception as e:
            print(f"Error stopping download: {e}")
            return False
    return False

def monitor_download(download_id, process):
    """监控下载进程"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        download = Download.query.get(download_id)
        if download:
            download.status = 'running'
            db.session.commit()
        
        # 等待进程结束
        process.wait()
        
        # 更新状态
        download = Download.query.get(download_id)
        if download:
            if process.returncode == 0:
                download.status = 'completed'
            else:
                download.status = 'failed'
            
            download.end_time = datetime.now()
            
            # 更新文件大小
            try:
                if os.path.exists(download.filepath):
                    download.filesize = os.path.getsize(download.filepath)
            except:
                pass
            
            db.session.commit()
        
        # 从字典中移除
        if str(download_id) in download_processes:
            del download_processes[str(download_id)]

def get_download_status(download_id):
    """获取下载状态"""
    download_id = str(download_id)
    if download_id in download_processes:
        process_info = download_processes[download_id]
        process = process_info['process']
        
        # 检查进程是否仍在运行
        if process.poll() is None:
            # 获取进程信息
            try:
                p = psutil.Process(process.pid)
                memory_info = p.memory_info()
                cpu_percent = p.cpu_percent(interval=0.1)
                
                # 计算运行时间
                runtime = (datetime.now() - process_info['start_time']).total_seconds()
                
                return {
                    'status': 'running',
                    'pid': process.pid,
                    'memory_mb': memory_info.rss / (1024 * 1024),
                    'cpu_percent': cpu_percent,
                    'runtime_seconds': runtime
                }
            except:
                return {'status': 'running', 'pid': process.pid}
        else:
            return {'status': 'stopped', 'returncode': process.returncode}
    
    return {'status': 'not_found'}