# -*- coding: utf-8 -*-
__author__ = 'gzp'

import os
from hashlib import md5
from django.test import TestCase
from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT
from django.core.files.uploadedfile import SimpleUploadedFile

from drf_attachment_upload.models import Attachment


class AttachmentUploadTestCase(TestCase):
    def setUp(self):
        self.api_url = '/api/attachments'
        self.file = SimpleUploadedFile('test', b'0' * 2 ** 25)
        self.md5 = ''

    def tearDown(self):
        try:
            attachment = Attachment.objects.get(md5=self.md5)
        except:
            pass
        else:
            attachment.delete_file()

    def test_attachment_upload(self):
        HTTP_CONTENT_RANGE = 'bytes {start}-{end}/{total}'
        chunk_size = 2097152
        md5_value = md5()
        while True:
            data_flow = self.file.read(chunk_size)  # 每次读入2M进入内存
            if not data_flow:  # 读取完后返回空值，False
                break
            md5_value.update(data_flow)
        self.md5 = md5_value.hexdigest()

        url = self.api_url + '/' + self.md5

        start = 0
        end = 0
        self.file.open('rb')
        while True:
            start = end
            end = start + chunk_size
            data_flow = self.file.read(chunk_size)
            if not data_flow or end >= self.file._size / 2:  # 模拟文件上传到一半断开连接
                break

            headers = {
                'HTTP_CONTENT_RANGE': HTTP_CONTENT_RANGE.format(
                    start=start,
                    end=end,
                    total=self.file._size
                )
            }
            res = self.client.put(url, encode_multipart(BOUNDARY, {
                'filename': self.file.name,
                'file': SimpleUploadedFile('test', data_flow)
            }), content_type=MULTIPART_CONTENT, **headers)
            self.assertEqual(res.status_code, 200)

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        status = 1  # 上传中的状态
        offset = res.json()['offset']
        start = offset
        end = offset
        self.file.open('rb')
        self.file.seek(offset)
        while True:
            start = end
            end = start + chunk_size
            data_flow = self.file.read(chunk_size)
            if not data_flow:
                break

            headers = {
                'HTTP_CONTENT_RANGE': HTTP_CONTENT_RANGE.format(
                    start=start,
                    end=end,
                    total=self.file._size
                )
            }
            res = self.client.put(url, encode_multipart(BOUNDARY, {
                'filename': self.file.name,
                'file': SimpleUploadedFile('test', data_flow)
            }), content_type=MULTIPART_CONTENT, **headers)
            self.assertEqual(res.status_code, 200)
            status = res.json()['status']
        self.assertEqual(status, 2)
