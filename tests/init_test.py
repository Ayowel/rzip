"""Test RZIP reproducible zip generation capabilities"""
import datetime
import hashlib
import os
import sys
import tempfile
import unittest.mock
import zipfile
import pytest
import rzip

@pytest.fixture(autouse=True)
def clear_env():
    """
    Remove environment configurations that may have side-effects on tests
    and/or be modified within them.
    """
    os.umask (0o077)
    os.environ.pop('SOURCE_DATE_EPOCH', None)

def test_simple_in_memory_build():
    """Test idempotence with simple dir/file creation"""
    with tempfile.SpooledTemporaryFile(mode='r+b') as tmpfile:
        with rzip.Rzip(tmpfile, compression = zipfile.ZIP_STORED) as f:
            f.create_directory('test1')
            f.create_directory('test2/')
            f.create_file('test3')
            f.create_file('test4', 'Hello world')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as zipinfo:
            filelist = zipinfo.filelist
            assert len(filelist) == 4
            for file in filelist:
                # By default, all files should be created at the ZIP EPOCH
                assert file.date_time == (1980, 1, 1, 0, 0, 0)
            assert filelist[0].filename == "test1/"
            assert filelist[1].filename == "test2/"
            assert filelist[2].filename == "test3"
            assert filelist[3].filename == "test4"
            assert filelist[0].file_size == 0
            assert filelist[1].file_size == 0
            assert filelist[2].file_size == 0
            assert filelist[3].file_size == len('Hello world')
            assert filelist[0].create_system
        tmpfile.seek(0)
        md5 = hashlib.md5(tmpfile.read()).hexdigest()
        assert md5 == 'd82bacdf59eeca800f0708a4c0cbec14'

@unittest.mock.patch('logging.error')
@unittest.mock.patch('logging.warning')
def test_source_date_epoch(logging_warning_mock, logging_error_mock):
    """Warn if parsing the SOURCE_DATE_EPOCH failed"""
    with tempfile.SpooledTemporaryFile(mode='r+b') as tmpfile:
        # Recheck default build
        os.environ.pop('SOURCE_DATE_EPOCH', None)
        with rzip.Rzip(tmpfile) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert f.filelist[0].date_time[0] == 1980
        logging_warning_mock.assert_not_called()
        tmpfile.flush()

        # Check invalid format logging
        os.environ['SOURCE_DATE_EPOCH'] = 'azeqsdgjhaze'
        with rzip.Rzip(tmpfile) as f:
            f.create_directory('test')
            assert logging_error_mock.call_count == 1
            logging_error_mock.reset_mock()
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert f.filelist[0].date_time[0] == 1980
        logging_warning_mock.assert_not_called()
        tmpfile.flush()

        # Check invalid date logging
        os.environ['SOURCE_DATE_EPOCH'] = str(3600*24*366*5)
        with rzip.Rzip(tmpfile) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            # Expect clamping to 1980 with a warning
            assert f.filelist[0].date_time[0] == 1980
        logging_error_mock.assert_not_called()
        logging_warning_mock.reset_mock()
        tmpfile.flush()

        # Check valid format logging
        os.environ['SOURCE_DATE_EPOCH'] = str(3600*24*366*15)
        with rzip.Rzip(tmpfile) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            # The EPOCH used for the calculation is 1970, so
            # we should only be 5 years after the ZIP epoch
            assert f.filelist[0].date_time[0] == 1985
        logging_error_mock.assert_not_called()
        logging_warning_mock.assert_not_called()

        # Check precedence with explicit zip date
        os.environ['SOURCE_DATE_EPOCH'] = str(3600*24*366*15)
        with rzip.Rzip(tmpfile, time = (2000, 1, 1, 0, 0, 0)) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert f.filelist[0].date_time[0] == 2000
        logging_error_mock.assert_not_called()
        logging_warning_mock.assert_not_called()

def test_timeformats():
    """Ensure that supported time formats work as intended"""
    with tempfile.SpooledTemporaryFile(mode='r+b') as tmpfile:
        # Unsupported time object
        with pytest.raises(ValueError) as _:
            with rzip.Rzip(tmpfile, time = True) as _:
                pass
        tmpfile.flush()

        if sys.version_info >= (3, 7):
            # Unsupported time string
            with pytest.raises(ValueError) as _:
                with rzip.Rzip(tmpfile, time = '2 eggs') as _:
                    pass
            tmpfile.flush()

            # Supported time string
            with rzip.Rzip(tmpfile, time = '1985-02-03') as f:
                f.create_directory('test')
            tmpfile.seek(0)
            with zipfile.ZipFile(tmpfile) as f:
                assert len(f.filelist) == 1
                assert f.filelist[0].date_time == (1985,2,3,0,0,0)
            tmpfile.flush()

        # Supported time list (too many items)
        with rzip.Rzip(tmpfile, time = (1990,1,1,0,0,0)) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert len(f.filelist[0].date_time) == 6
            assert f.filelist[0].date_time == (1990,1,1,0,0,0)
        tmpfile.flush()

        # Supported time list (too many items)
        with rzip.Rzip(tmpfile, time = (1995,1,1,0,0,0,0)) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert len(f.filelist[0].date_time) == 6
            assert f.filelist[0].date_time == (1995,1,1,0,0,0)
        tmpfile.flush()

        # Supported time list (too few items)
        with rzip.Rzip(tmpfile, time = [2000]) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert len(f.filelist[0].date_time) == 6
            assert f.filelist[0].date_time == (2000,1,1,0,0,0)
        tmpfile.flush()

        # Supported date object
        with rzip.Rzip(tmpfile, time = datetime.datetime(2005, 2, 3)) as f:
            f.create_directory('test')
        tmpfile.seek(0)
        with zipfile.ZipFile(tmpfile) as f:
            assert len(f.filelist) == 1
            assert len(f.filelist[0].date_time) == 6
            assert f.filelist[0].date_time == (2005,2,3,0,0,0)
        tmpfile.flush()
