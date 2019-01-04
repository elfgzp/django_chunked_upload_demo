# -*- coding: utf-8 -*-
__author__ = 'gzp'

import re

from django.core.files.base import ContentFile

from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response

from .models import Attachment
from .serializers import AttachmentSerializer
from .exceptions import (
    NoChunkFileErr, RequestHeaderErr, ChunkSizeErr, OffsetNotMatchErr,
    UploadIsCompletedErr
)


class AttachmentViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    field_name = 'file'
    content_range_pattern = re.compile(
        r'^bytes (?P<start>\d+)-(?P<end>\d+)/(?P<total>\d+)$'
    )

    model = Attachment
    serializer_class = AttachmentSerializer

    lookup_field = 'md5'

    def get_queryset(self):
        return self.model.objects.all()

    def _put_chunk(self, request, md5, *args, **kwargs):
        try:
            chunk = request.data[self.field_name]
        except KeyError:
            raise NoChunkFileErr()

        filename = request.data.get('filename')

        content_range = request.META.get('HTTP_CONTENT_RANGE', '')
        match = self.content_range_pattern.match(content_range)
        if not match:
            raise RequestHeaderErr()

        start = int(match.group('start'))
        end = int(match.group('end'))
        total = int(match.group('total'))

        chunk_size = end - start

        if chunk.size != chunk_size:
            raise ChunkSizeErr(chunk.size, chunk_size)

        attachment = self._get_attachment(md5)

        if not attachment:
            attachment = self._create_attachment(md5, total, filename)

        self.is_valid_attachment(attachment)
        if attachment.offset != start:
            raise OffsetNotMatchErr()

        attachment.append_chunk(chunk, chunk_size=chunk_size)

        attachment.user_id = request.user if request.user.is_authenticated else None
        attachment.offset = end
        attachment.filename = filename

        attachment.save()

        return attachment

    def _create_attachment(self, md5, size, filename=None):
        attachment = self.model(md5=md5, size=size, filename=filename)
        attachment.file.save(filename, ContentFile(''))
        attachment.save()
        return attachment

    def _get_attachment(self, md5):
        try:
            return self.model.objects.get(md5=md5)
        except self.model.DoesNotExist:
            return None

    @classmethod
    def is_valid_attachment(cls, attachment):
        """
        Check if chunked upload has already expired or is already complete.
        """

        pass

    def update(self, request, md5=None, *args, **kwargs):
        attachment = self._put_chunk(request, md5=md5, *args, **kwargs)
        return Response(
            self.serializer_class(attachment, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
