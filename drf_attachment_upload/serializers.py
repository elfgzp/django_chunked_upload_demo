# -*- coding: utf-8 -*-
__author__ = 'gzp'

from rest_framework import serializers
from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('md5', 'file', 'filename', 'user_id', 'offset', 'created_at', 'status', 'completed_at')
