# -*- coding: utf-8 -*-
__author__ = 'gzp'

import os

from hashlib import md5

from django.core.files.base import ContentFile

from django.db import models, transaction
from django.utils import timezone
from django import conf

from .settings import (
    UPLOAD_PATH,
    STORAGE
)

from .exceptions import CompletedFileMD5NotMatch


def generate_filename(instance, filename):
    return os.path.join(os.path.join(UPLOAD_PATH, instance.md5), filename)


class Attachment(models.Model):
    UPLOADING = 1
    COMPLETED = 2
    STATUS_CHOICES = (
        (UPLOADING, 'Incomplete'),
        (COMPLETED, 'Complete'),
    )
    md5 = models.CharField(max_length=32, unique=True)
    file = models.FileField(
        upload_to=generate_filename,
        storage=STORAGE,
        null=True
    )
    filename = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.ForeignKey(
        conf.settings.AUTH_USER_MODEL,
        editable=False,
        on_delete=models.SET_NULL,
        null=True
    )
    offset = models.BigIntegerField(default=0)
    size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=UPLOADING)
    completed_at = models.DateTimeField(null=True,
                                        blank=True)

    def delete_file(self):
        if self.file:
            storage, path = self.file.storage, self.file.path
            storage.delete(path)
        self.file = None

    @transaction.atomic
    def delete(self, delete_file=True, *args, **kwargs):
        super(Attachment, self).delete(*args, **kwargs)
        if delete_file:
            self.delete_file()

    def append_chunk(self, chunk, chunk_size=None, save=True):
        mode = 'ab' if self.offset != 0 else 'wb'
        self.file.close()
        try:
            self.file.open(mode=mode)
        except ValueError:
            self.file.save(self.filename, ContentFile(''))
            self.file.open(mode=mode)

        for sub_chunk in chunk.chunks():
            self.file.write(sub_chunk)
        if chunk_size is not None:
            self.offset += chunk_size
        elif hasattr(chunk, 'size'):
            self.offset += chunk.size
        else:
            self.offset = self.file.size
        if save:
            self.save()
        self.file.close()

    def completed(self):
        if self.file:
            try:
                real_md5 = self.md5_calc()
            except ValueError:
                self.delete()
                raise CompletedFileMD5NotMatch
            else:
                if self.md5 == real_md5:
                    self.status = self.COMPLETED
                    self.completed_at = timezone.now()
                else:
                    self.delete()
                    raise CompletedFileMD5NotMatch
        else:
            self.delete()

    def md5_calc(self):
        self.file.close()
        md5_value = md5()
        self.file.open('rb')
        while True:
            data_flow = self.file.read(2097152)  # 每次读入2M进入内存
            if not data_flow:  # 读取完后返回空值，False
                break
            md5_value.update(data_flow)
        self.file.close()
        return md5_value.hexdigest()

    def save(self, *args, **kwargs):
        if self.offset == self.size and self.status != self.COMPLETED:
            self.completed()

        return super(Attachment, self).save(*args, **kwargs)

    def __str__(self):
        return '<filename: %s - md5: %s - bytes: %s - status: %s>' % (
            self.filename, self.md5, self.offset, self.status)
