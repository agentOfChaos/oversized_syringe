import argparse


def parsecli():
    parser = argparse.ArgumentParser(description="Hyperdimension Neptunia .pac packer / unpacker")
    parser.add_argument('--raw', help='do not decompress the extrated files', action='store_true')
    parser.add_argument('--list', '-l', help='just list the content of the file', action='store_true')
    parser.add_argument('--extract', '-x', metavar='location', help='set the directory to extract the files to.'
                        ' If single files are not specified, extract the whole package', type=str)
    parser.add_argument('--list-harder', '-L', help='list in detail the content of the file', action='store_true')
    parser.add_argument('--extract-id', metavar='id,list', help='extract files specified by id', type=str)
    parser.add_argument('--file-info', metavar='id', help='print detailed information about a specific file', type=int)
    parser.add_argument('--test-add', metavar='file', help='add a new file to the package', type=str)
    parser.add_argument('--output', '-o', metavar='pac', help='create a new copy of the archive, save modifies',
                        type=str)
    parser.add_argument('--dry-run', '-D', help='Applies to packing, not unpacking; do everything, create files/'
                        'directories, except nothing is actually written', action='store_true')
    parser.add_argument('--merge', '-m', metavar='dir', help='Merge the content of target directory as a new pac-file',
                        type=str)

    parser.add_argument('file', metavar='filename', help='.pac file to extract from / directory to compress')
    return parser.parse_args()