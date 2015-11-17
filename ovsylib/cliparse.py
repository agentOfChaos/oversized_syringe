import argparse


def parsecli():
    parser = argparse.ArgumentParser(description="Hyperdimension Neptunia .pac packer / unpacker")
    parser.add_argument('--raw', help='do not decompress the extrated files', action='store_true')
    parser.add_argument('--list', '-l', help='list the content of the file / staging environment', action='store_true')
    parser.add_argument('--extract', '-x', metavar='location', help='set the directory to extract the files to.'
                        ' If single files are not specified, extract the whole package', type=str)
    parser.add_argument('--list-harder', '-L', help='list in detail the content of the file', action='store_true')
    parser.add_argument('--extract-id', metavar='id,list', help='extract files specified by id', type=str)
    parser.add_argument('--file-info', metavar='id', help='print detailed information about a specific file', type=int)
    parser.add_argument('--dry-run', '-D', help='Applies to packing, not unpacking; do everything, create files/'
                        'directories, except nothing is actually written', action='store_true')
    parser.add_argument('--debug', help='Turn debug messages on; also, save eventual huffman trees to dot files',
                        action="store_true")
    parser.add_argument('--no-compress', '-N', help='do not compress added files', action='store_true')

    parser.add_argument('--stage', '-S', help='engage staging mode (git-like modification environment); '
                        'if you provide a pac file name, it will be used as a base for future modifies;'
                        ' otherwise (no parameters), a fresh new pacfile will be created',
                        action='store_true')
    parser.add_argument('--add', '-a', help='(staging only) stage add a file; if a base-directory is'
                        ' specified, the file\'s internal name will be calculated relatively to said path',
                        action='store_true')
    parser.add_argument('--base-dir', '-B', metavar='basedir', help='(optional) set a base directory, useful for'
                        ' computing relative filepaths',
                        type=str, default='.')
    parser.add_argument('--merge', '-m', help='(staging only) merge the content of a directory into the package,'
                        ' old files will be replaced', action='store_true')
    parser.add_argument('--undo', '-u', help='(staging only) undo the modifies staged for the specified filename',
                        action='store_true')
    parser.add_argument('--remove', '-r', help='(staging only) stage remove the file with the specified filename'
                        ' if the file was staged for adding, the adding will be canceled',
                        action='store_true')
    parser.add_argument('--commit', '-c', help='(staging only) apply the staged commits; the staging environment'
                        ' will now contain only a freshly modified pacfile object, ready to be written to disk',
                        action='store_true')
    parser.add_argument('--write', '-w', help='(staging only) create a new pacfile from the staged object; the file'
                        ' name must be provided',
                        action='store_true')
    parser.add_argument('--peek', '-P', help='(staging only) peek into the pacfile object stored into the staging'
                        ' environment; this enables you to use the listing/extraction commands on it. If you plan'
                        ' to extract, make sure the \'target\' variable points to a real .pac file on disk',
                        action='store_true')

    parser.add_argument('file', metavar='filename', help='target file/folder to extract from/import into', nargs='?')
    return parser.parse_args()