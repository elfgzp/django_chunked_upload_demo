# -*- coding: utf-8 -*-
__author__ = 'gzp'


class NoChunkFileErr(Exception):

    def __init__(self):
        self.msg = 'No chunk file was submitted'


class RequestHeaderErr(Exception):
    def __init__(self):
        self.msg = 'Error in request headers'


class ChunkSizeErr(Exception):
    def __init__(self, chunk_size, err_chunk_size):
        self.msg = "File size doesn't match headers: file size is {} but {} reported".format(
            chunk_size, err_chunk_size)


class OffsetNotMatchErr(Exception):
    def __init__(self):
        self.msg = 'Offsets do not match'


class UploadIsCompletedErr(Exception):
    def __init__(self):
        self.msg = 'Upload has already been marked as Completed'


class CompletedFileMD5NotMatch(Exception):
    def __init__(self):
        self.msg = 'Completed file MD5 not match'
