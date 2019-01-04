# -*- coding: utf-8 -*-
__author__ = 'gzp'

from django.conf import settings

DEFAULT_UPLOAD_PATH = 'attachments/'

UPLOAD_PATH = getattr(settings, 'DRF_ATTACHMENT_UPLOAD_PATH', DEFAULT_UPLOAD_PATH)

STORAGE = getattr(settings, 'DRF_ATTACHMENT_UPLOAD_STORAGE_CLASS', lambda: None)()
