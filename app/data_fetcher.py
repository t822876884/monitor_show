import requests
import json
from datetime import datetime
from app import db
from app.models import Platform, Livestream
import time


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
        """获取指定平台的直播间列表，并带有重试逻辑"""
        stream_url = f"http://api.hclyz.com:81/mf/{platform_address}"
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                response = requests.get(stream_url)

                if response.status_code == 200:
                    data = response.json()

                    # 更新数据库中的直播间信息
                    active_stream_ids = []
                    for stream in data.get('zhubo', []):
                        stream_id = f"{platform_id}_{stream.get('title')}"
                        active_stream_ids.append(stream_id)
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
                    return True  # 成功获取数据，退出函数

                elif response.status_code == 502:
                    print(
                        f"Attempt {attempt + 1}/{max_retries}: Received 502 error for {platform_address}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)

                else:
                    print(f"Failed to fetch livestreams from {platform_address}: Status code {response.status_code}")
                    return False  # 其他错误，直接退出

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}/{max_retries}: Request exception for {platform_address}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        print(f"Failed to fetch livestreams for {platform_address} after {max_retries} attempts.")
        return False