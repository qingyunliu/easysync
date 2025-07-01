from abc import ABC, abstractmethod
import boto3
import oss2
from obs import ObsClient

class StorageProvider(ABC):
    """存储提供者基类"""
    
    @abstractmethod
    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20):
        """列出对象"""
        pass

    @abstractmethod
    def get_object(self, bucket: str, key: str):
        """获取对象"""
        pass

    @abstractmethod
    def put_object(self, bucket: str, key: str, data):
        """上传对象"""
        pass

    @abstractmethod
    def delete_object(self, bucket: str, key: str):
        """删除对象"""
        pass

class S3Provider(StorageProvider):
    """S3存储提供者"""
    
    def __init__(self, config):
        self.client = boto3.client(
            's3',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            endpoint_url=config.get('endpoint'),
            region_name=config.get('region')
        )

    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20):
        try:
            # 计算起始位置
            start = (page - 1) * page_size
            
            # 获取所有对象
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket,
                Prefix=prefix
            )
            
            # 获取总数和分页数据
            objects = []
            total = 0
            for page in page_iterator:
                if 'Contents' in page:
                    total += len(page['Contents'])
                    if total > start and len(objects) < page_size:
                        for obj in page['Contents']:
                            if len(objects) < page_size:
                                objects.append({
                                    'key': obj['Key'],
                                    'size': obj['Size'],
                                    'last_modified': obj['LastModified'].isoformat()
                                })
            
            return {
                'objects': objects,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            raise Exception(f'列出对象失败: {str(e)}')

    def get_object(self, bucket: str, key: str):
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            raise Exception(f'获取对象失败: {str(e)}')

    def put_object(self, bucket: str, key: str, data):
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=data)
        except Exception as e:
            raise Exception(f'上传对象失败: {str(e)}')

    def delete_object(self, bucket: str, key: str):
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
        except Exception as e:
            raise Exception(f'删除对象失败: {str(e)}')

class OSSProvider(StorageProvider):
    """阿里云OSS存储提供者"""
    
    def __init__(self, config):
        self.auth = oss2.Auth(config['access_key'], config['secret_key'])
        self.endpoint = config['endpoint']

    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20):
        try:
            bucket_instance = oss2.Bucket(self.auth, self.endpoint, bucket)
            
            # 计算起始位置
            start = (page - 1) * page_size
            
            # 获取所有对象
            objects = []
            total = 0
            for obj in oss2.ObjectIterator(bucket_instance, prefix=prefix):
                total += 1
                if total > start and len(objects) < page_size:
                    objects.append({
                        'key': obj.key,
                        'size': obj.size,
                        'last_modified': obj.last_modified.isoformat()
                    })
            
            return {
                'objects': objects,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            raise Exception(f'列出对象失败: {str(e)}')

    def get_object(self, bucket: str, key: str):
        try:
            bucket_instance = oss2.Bucket(self.auth, self.endpoint, bucket)
            return bucket_instance.get_object(key).read()
        except Exception as e:
            raise Exception(f'获取对象失败: {str(e)}')

    def put_object(self, bucket: str, key: str, data):
        try:
            bucket_instance = oss2.Bucket(self.auth, self.endpoint, bucket)
            bucket_instance.put_object(key, data)
        except Exception as e:
            raise Exception(f'上传对象失败: {str(e)}')

    def delete_object(self, bucket: str, key: str):
        try:
            bucket_instance = oss2.Bucket(self.auth, self.endpoint, bucket)
            bucket_instance.delete_object(key)
        except Exception as e:
            raise Exception(f'删除对象失败: {str(e)}')

class OBSProvider(StorageProvider):
    """华为云OBS存储提供者"""
    
    def __init__(self, config):
        self.client = ObsClient(
            access_key_id=config['access_key'],
            secret_access_key=config['secret_key'],
            server=config['endpoint']
        )

    def list_objects(self, bucket: str, prefix: str = '', page: int = 1, page_size: int = 20):
        try:
            # 计算起始位置
            start = (page - 1) * page_size
            
            # 获取所有对象
            objects = []
            total = 0
            marker = ''
            while True:
                resp = self.client.listObjects(bucket, prefix=prefix, marker=marker)
                if resp.status < 300:  # 请求成功
                    if resp.body.contents:
                        for obj in resp.body.contents:
                            total += 1
                            if total > start and len(objects) < page_size:
                                objects.append({
                                    'key': obj.key,
                                    'size': obj.size,
                                    'last_modified': obj.lastModified.isoformat()
                                })
                    
                    if not resp.body.isTruncated:
                        break
                    marker = resp.body.nextMarker
                else:
                    raise Exception(f'列出对象失败: {resp.reason}')
            
            return {
                'objects': objects,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            raise Exception(f'列出对象失败: {str(e)}')

    def get_object(self, bucket: str, key: str):
        try:
            resp = self.client.getObject(bucket, key)
            if resp.status < 300:  # 请求成功
                return resp.body.read()
            else:
                raise Exception(f'获取对象失败: {resp.reason}')
        except Exception as e:
            raise Exception(f'获取对象失败: {str(e)}')

    def put_object(self, bucket: str, key: str, data):
        try:
            resp = self.client.putObject(bucket, key, data)
            if resp.status >= 300:  # 请求失败
                raise Exception(f'上传对象失败: {resp.reason}')
        except Exception as e:
            raise Exception(f'上传对象失败: {str(e)}')

    def delete_object(self, bucket: str, key: str):
        try:
            resp = self.client.deleteObject(bucket, key)
            if resp.status >= 300:  # 请求失败
                raise Exception(f'删除对象失败: {resp.reason}')
        except Exception as e:
            raise Exception(f'删除对象失败: {str(e)}')