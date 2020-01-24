# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import *


class FDFSStorage(Storage):
    """fast_dfs文件存储类"""

    def __init__(self, client_conf=None, base_url=None):
        if client_conf == None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url == None:
            base_url = settings.FDFS_STORAGE_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        """打开文件时使用"""
        pass

    def _save(self, name, content):
        """文件存储时使用"""
        # 创建一个fdfs client对象
        tracker = get_tracker_conf(self.client_conf)
        client = Fdfs_client(tracker)

        # 上传文件到fastdfs系统中
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fastdfs失败')

        # 上传成功，获取返回的文件id
        filename = res.get('Remote file_id')

        return filename.decode()

    def exists(self, name):
        """django判断文件名是否可用"""
        return False

    def url(self, name):
        """返回访问文件的url路径"""
        return self.base_url + name