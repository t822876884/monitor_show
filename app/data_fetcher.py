import requests
import json
from datetime import datetime
from app import db
from app.models import Platform, Livestream

class DataFetcher:
    def __init__(self, api_url):
        self.api_url = api_url
    
    def fetch_platforms(self):
        """获取平台列表"""
        try:
            response = requests.get(self.api_url)
            data = response.json()
            
            # 更新数据库中的平台信息
            for platform in data.get('pingtai', []):
                platform_id = platform.get('address').split('.')[0]
                existing = Platform.query.filter_by(platform_id=platform_id).first()
                
                if existing:
                    existing.title = platform.get('title')
                    existing.address = platform.get('address')
                    existing.img = platform.get('xinimg')
                    existing.number = platform.get('Number')
                else:
                    new_platform = Platform(
                        platform_id=platform_id,
                        title=platform.get('title'),
                        address=platform.get('address'),
                        img=platform.get('xinimg'),
                        number=platform.get('Number')
                    )
                    db.session.add(new_platform)
                
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error fetching platforms: {e}")
            return False
    
    def fetch_livestreams(self, platform_id, platform_address):
        """获取指定平台的直播间列表"""
        try:
            stream_url = f"http://api.hclyz.com:81/mf/{platform_address}"
            response = requests.get(stream_url)
            data = response.json()
            
            # 更新数据库中的直播间信息
            for stream in data.get('zhubo', []):
                stream_id = f"{platform_id}_{stream.get('title')}"
                existing = Livestream.query.filter_by(stream_id=stream_id).first()
                
                if existing:
                    existing.title = stream.get('title')
                    existing.address = stream.get('address')
                    existing.img = stream.get('img')
                    existing.is_online = True
                    existing.last_check = datetime.now()
                else:
                    new_stream = Livestream(
                        stream_id=stream_id,
                        platform_id=platform_id,
                        title=stream.get('title'),
                        address=stream.get('address'),
                        img=stream.get('img'),
                        is_online=True,
                        last_check=datetime.now()
                    )
                    db.session.add(new_stream)
                
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error fetching livestreams: {e}")
            return False