#!/usr/bin/env python3
"""
Build a zip by running the module directly.
"""
import argparse
import glob
import itertools
import logging
import mmap
import os
import sys
import zipfile
import repzip as rzip

COMPRESSION_ALGORITHMS = ['stored', 'deflated']
if sys.version_info >= (3,3):
    COMPRESSION_ALGORITHMS.append('bzip2')
    COMPRESSION_ALGORITHMS.append('lzma')

EXE_MAGICS = [
    b'#!', # Executable script
    b'\x7FELF',  # Binary executable
    b'MZ', # MS-DOS Executable
    b'\xca\xfe\xba\xbe', # MAC executable
]

def build_parser():
    """
    Creates the argument parser and returns it.
    """
    parser = argparse.ArgumentParser(
        prog="repzip",
        description="A python library to easily generate reproducible zip archives",
        epilog="\n".join((
            "repzip {}. Learn more on reproducible builds at https://reproducible-builds.org/.".format(rzip.__version__),
        )),
    )
    # pylint: disable=line-too-long
    parser.add_argument('out_file', help="Output zip file path.")
    parser.add_argument('pattern', nargs = '+', help="File/directory pattern to add to the zip file. Prefix with ! to negate a path.")
    parser.add_argument('--file', '-f', help="Source file to extract patterns from.")
    parser.add_argument('--compression', '-c', choices=COMPRESSION_ALGORITHMS, default='deflated', help="The compression algorithm to use. Make sure that the corresponding libraries are installed.")
    parser.add_argument('--compress-level', '-C', type=int, help="(Python 3.7+) The compression level to use. Only has an effect if the compression used is 'deflated' or 'bzip2'.")
    parser.add_argument('--perm', '-p', action='append', help="Set files permissions. A pattern to the files affected by the change may be provided in the form perm=pattern.")
    parser.add_argument('--umask', '-u', help="Default umask to apply to all files/directories.")
    parser.add_argument('--time', '-t', help="(Python 3.7+) Default time to use for all files (in the ISO format).")
    parser.add_argument('--recurse', '-r', default=False, action='store_true', help="Also add matched directories content.")
    parser.add_argument('--root', '-R', help="Base path from which all input files searched for.")
    # pylint: enable=line-too-long
    return parser

def build_zip(args):
    """
    Build the ZIP file
    """
    if args.root:
        assert os.path.isdir(args.root)
    if sys.version_info < (3, 7) and args.compress_level:
        logging.warning("A compression level was provided but it will be ignored due to python being on an old version.")

    original_directory = os.getcwd()
    added_paths = set()
    compression = getattr(zipfile, 'ZIP_{}'.format(args.compression.upper()))
    # pylint: disable-next=line-too-long
    rzip_args = {
        'compression': compression,
        'compresslevel': args.compress_level,
        'mask': args.umask,
        'time': args.time,
    }
    with rzip.Rzip(args.out_file, **rzip_args) as handle:
        if args.root:
            logging.debug("Change directory to %s", args.root)
            os.chdir(args.root)
        try:
            for pattern in args.pattern:
                if sys.version_info < (3, 5):
                    if '**' in pattern:
                        logging.warning("Pattern contains recursive glob, this is a Python 3.5+ feature (%s)", pattern)
                    glob_match = sorted(glob.glob(pattern))
                else:
                    glob_match = sorted(glob.glob(pattern, recursive=True))
                if not glob_match:
                    raise ValueError("Pattern did not match any file ({})".format(pattern))
                i = 0
                while i < len(glob_match):
                    path = glob_match[i]
                    i+=1
                    abs_path = os.path.abspath(path)
                    if abs_path in added_paths:
                        continue
                    added_paths.add(abs_path)
                    if os.path.isdir(path):
                        zip_path = path if path.endswith('/') else "{}/".format(path)
                        handle.create_directory(zip_path, compression=zipfile.ZIP_STORED)
                        if args.recurse:
                            for root, dirs, files in os.walk(path):
                                dirs.sort()
                                files.sort()
                                for ipath in itertools.chain(dirs, files):
                                    glob_match.append(os.path.join(root, ipath))
                    elif os.path.isfile(path):
                        with open(path, 'rb') as fref:
                            with mmap.mmap(fref.fileno(), 0, access = mmap.ACCESS_READ) as fmap:
                                handle.create_file(path, fmap, compression=zipfile.ZIP_STORED if len(fmap) == 0 else compression)
                    else:
                        logging.warning("Ignoring %s: not a supported inode type", path)
        finally:
            if args.root:
                logging.debug("Reset directory to %s", original_directory)
                os.chdir(original_directory)

def main():
    """Entrypoint used when the script is called"""
    try:
        build_zip(build_parser().parse_args())
    # pylint: disable=broad-except
    except Exception as exc:
        logging.error("An error occured: %s", exc)
        sys.exit(1)
    # pylint: enable=broad-except

if __name__ == '__main__':
    main()
