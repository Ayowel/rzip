"""Test the __main__ rzip entrypoint"""
import hashlib
import os
import random
import tempfile
import zipfile
import pytest
import repzip.__main__ as rzipmain # pylint: disable=no-name-in-module,import-error

@pytest.fixture(autouse=True)
def clear_env():
    """
    Remove environment configurations that may have side-effects on tests
    and/or be modified within them.
    """
    os.umask (0o077)
    os.environ.pop('SOURCE_DATE_EPOCH', None)

def build_reference_directory(rootdir):
    """
    Standardize & randomize zipped path layout for test consumption
    """
    def make_test1():
        os.mkdir(os.path.join(rootdir, 'test1'))
        def make_test1_subfile():
            with open(os.path.join(rootdir, 'test1', 'subtest_file'), 'wb') as f:
                f.write(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        subdirs = [
            lambda: os.mkdir(os.path.join(rootdir, 'test1', 'subtest')),
            lambda: os.mkdir(os.path.join(rootdir, 'test1', 'subtest2')),
            make_test1_subfile,
        ]
        random.shuffle(subdirs)
        for l in subdirs:
            l()
        subdirs = [
            lambda: os.mkdir(os.path.join(rootdir, 'test1', 'subtest', 'subsubtest1')),
            lambda: os.mkdir(os.path.join(rootdir, 'test1', 'subtest', 'subsubtest2')),
            lambda: os.mkdir(os.path.join(rootdir, 'test1', 'subtest', 'subsubtest3')),
        ]
        random.shuffle(subdirs)
        for l in subdirs:
            l()
        os.chmod(os.path.join(rootdir, 'test1', 'subtest', 'subsubtest2'), 0o0777)
    def make_test2():
        with open(os.path.join(rootdir, 'test2'), 'wb') as f:
            f.write(b'Hell world.')
    def make_test3():
        with open(os.path.join(rootdir, 'test3'), 'wb') as f:
            f.write(b'Hella world.')
        os.chmod(os.path.join(rootdir, 'test3'), 0o0777)
    paths_builders = [make_test1, make_test2, make_test3]
    random.shuffle(paths_builders)
    for c in paths_builders:
        c()


# pylint: disable-next=protected-access
@pytest.mark.parametrize('compression', rzipmain.COMPRESSION_ALGORITHMS)
def test_rooted_on_disk_cmd(compression):
    """Zip the content of a directory on disk"""
    expected_checksum = {
        'stored': 'cdc4594a32c159c8009c4d075279afcd',
        'deflated': '83a61a645686a638e8e6d09aea6dd8a8',
        'bzip2': '3b4393c59b62df398cd3a504f273ed42',
        'lzma': '01e4efdf0cc6d0ea5ceb44d90260fa6d',
    }
    with tempfile.TemporaryDirectory() as rootdir:
        build_reference_directory(rootdir)
        parser = rzipmain.build_parser()
        with tempfile.TemporaryDirectory() as outdir:
            outfile = os.path.join(outdir, 'out.zip')
            args = ['--root', rootdir, '-r', '--compression', compression, outfile, '*']
            parsed_args = parser.parse_args(args)
            # TODO: run script & validate resulting zip
            rzipmain.build_zip(parsed_args)
            with zipfile.ZipFile(outfile, 'r') as zipinfo:
                assert len(zipinfo.filelist) == 9
                filenames = [f.filename for f in zipinfo.filelist]
                assert 'test1/' in filenames
                assert 'test1/subtest/' in filenames
                assert 'test1/subtest_file' in filenames
                assert 'test1/subtest/subsubtest1/' in filenames
                assert 'test1/subtest/subsubtest2/' in filenames
                assert 'test1/subtest/subsubtest3/' in filenames
                assert 'test1/subtest2/' in filenames
                assert 'test2' in filenames
                assert 'test3' in filenames
            with open(outfile, 'rb') as f:
                zipdata = f.read()
            md5 = hashlib.md5(zipdata).hexdigest()
            assert md5 == expected_checksum[compression]
