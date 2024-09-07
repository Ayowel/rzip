#!/usr/bin/env python3
"""
Build zip archives reproducibly
"""

from datetime import datetime, timezone
import logging
import os
import stat
import sys
import zipfile

__version__ = "0.1.0"

ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

class Rzip:
    """
    Create a new zip file
    """

    def __init__(self, file, compression = zipfile.ZIP_DEFLATED, compresslevel = None, mask = None, time = None):
        """
        Returns
        =======
        A stream of bytes (the zip's content)
        """
        self.compression = compression
        self.compressionlevel = compresslevel
        self.timestamp = None
        self.umask = mask if mask is not None else 0o0027
        if time is not None:
            self.timestamp = self._get_timestamp(time)
        # pylint: disable=consider-using-with
        if sys.version_info >= (3, 7):
            # pylint: disable=unexpected-keyword-arg
            self.zip = zipfile.ZipFile(file, mode = 'w', compression=self.compression, compresslevel=self.compressionlevel)
            # pylint: enable=unexpected-keyword-arg
        else:
            self.zip = zipfile.ZipFile(file, mode = 'w', compression=self.compression)
        # pylint: enable=consider-using-with

    # pylint: disable=too-many-return-statements
    def _get_timestamp(self, time = None):
        """
        Get a tuple that represents the time provided as parameter
        or the default zip time.
        """
        if time is None:
            if self.timestamp is not None:
                return self.timestamp
            source_date_epoch = os.environ.get('SOURCE_DATE_EPOCH', None)
            if source_date_epoch:
                try:
                    date = datetime.fromtimestamp(int(source_date_epoch), tz = timezone.utc)
                except ValueError:
                    # pylint: disable=line-too-long
                    logging.error("Failed to parse SOURCE_DATE_EPOCH despite it being set (%s). Default epoch will be used instead.", source_date_epoch)
                    # pylint: enable=line-too-long
                else:
                    if date.year < 1980:
                        # pylint: disable=line-too-long
                        logging.warning("SOURCE_DATE_EPOCH is set to before 1980, which the ZIP format does not support. Clamping date to 1980.")
                        # pylint: enable=line-too-long
                        return ZIP_EPOCH
                    return (date.year, date.month, date.day, date.hour, date.minute, date.second)
            return ZIP_EPOCH
        if isinstance(time, (tuple, list)):
            date = time
            date_len = len(date)
            if date_len == 6:
                return date
            for i in range(5):
                if date_len == i:
                    return (*date, *ZIP_EPOCH[i:])
            return date[:6]
        if isinstance(time, str) and sys.version_info >= (3,7):
            date = datetime.fromisoformat(time)
            return (date.year, date.month, date.day, date.hour, date.minute, date.second)
        if isinstance(time, datetime):
            return (time.year, time.month, time.day, time.hour, time.minute, time.second)
        raise ValueError("Received an unsupported time object.")
    # pylint: enable=too-many-return-statements

    def create_directory(self, path, permissions = None, data = b'', compression = None):
        """
        Explicitely create a directory in the archive.
        This should only be used if the directory is empty or needs
        specific permissions.

        @param data
            Associate data to the created directory. This is a useless
            parameter unless you're building a ctf of some sort or trying to hide information.
        """
        if os.path.sep != '/':
            path = path.replace(os.path.sep, '/')
        if not path.endswith('/'):
            path += '/'
        info = zipfile.ZipInfo(path, self._get_timestamp())
        info.create_system = 3 # Do not differentiate between windows & linux systems
        perms = permissions if permissions is not None else (0o0777 ^ self.umask)
        info.external_attr = ((stat.S_IFDIR|perms) << 16) | 0x10 # MS-DOS directory flag
        info.compress_type = compression if compression is not None else zipfile.ZIP_STORED
        self.zip.writestr(info, data)

    def create_file(self, path, data = b'', permissions = None, compression = None):
        """
        Write a file into the archive.  The contents is 'data', which
        may be either a 'str' or a 'bytes' instance; if it is a 'str',
        it is encoded as UTF-8 first.
        """
        if os.path.sep != '/':
            path = path.replace(os.path.sep, '/')
        info = zipfile.ZipInfo(path, self._get_timestamp())
        info.create_system = 3 # Do not differentiate between windows & linux systems
        perms = permissions if permissions is not None else (0o0666 & (0o7777^ self.umask))
        info.external_attr =  (stat.S_IFREG|perms) << 16
        info.compress_type = compression if compression is not None else self.compression
        self.zip.writestr(info, data)

    def close(self):
        """Close the file, and write the ending records."""
        self.zip.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

__all__ = ('Rzip',)
