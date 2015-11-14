#!/usr/bin/python

from ovsylib import cliparse, datastruct
import os


def main(cmdline):
    with open(cmdline.file, "rb") as binfile:
        pac = datastruct.pacfile()
        pac.loadFromFile(binfile)

        if cmdline.list:
            pac.printInfo()
        elif cmdline.list_harder:
            pac.printDetailInfo()
        elif cmdline.extract_id:
            idlist = map(int, cmdline.extract_id.split(","))
            if cmdline.raw:
                location = datastruct.adjustSeparatorForFS("raw-extract/")
                if cmdline.extract:
                    location = cmdline.extract_id
                for fid in idlist:
                    pac.dumpFileId(fid, location, binfile)
            else:
                location = datastruct.adjustSeparatorForFS("extract/")
                if cmdline.extract:
                    location = cmdline.extract_id
                for fid in idlist:
                    pac.extractFileId(fid, location, binfile)
        elif cmdline.extract:
            for fid in range(len(pac.files)):
                pac.extractFileId(fid, cmdline.extract, binfile)
        elif cmdline.file_info:
            file = pac.getFileById(cmdline.file_info)
            if file is not None:
                print("          id    offset       size  compress  size  filename")
                file.printDetailInfo()

        if cmdline.merge:
            pass

        if cmdline.test_add:
            if os.path.isfile(cmdline.test_add_1):
                newfile = datastruct.fileentry()
                internalname = cmdline.test_add.replace("/","\\")
                newfile.createFromFile(cmdline.test_add, cmdline.test_add, adjust_separator=True)
                pac.appendFile(newfile)
                pac.printInfo()
                print("Added file \"" +  cmdline.test_add+ "\" as \"" + internalname + "\"; offset and compressed "
                      "size will be determined at write-time")
            else:
                print("cannot find file " + cmdline.test_add)

        if cmdline.output:
            pac.createCopy(binfile, cmdline.output, dry_run=cmdline.dry_run)


if __name__ == '__main__':
    commandline = cliparse.parsecli()
    main(commandline)