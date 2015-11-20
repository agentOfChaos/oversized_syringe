#!/usr/bin/python

from ovsylib import cliparse, datastruct, fileadding_utils
from ovsylib.aggressive_threading import Broker
import os


def extractJob(pac, fid, cmdline, filename):
    with open(filename, "rb") as binfile:
        pac.extractFileId(fid, cmdline.extract, binfile, debuggy=cmdline.debug)


def nonStaging(pac, cmdline, filename):
    if cmdline.list:
        pac.printInfo()

    elif cmdline.list_harder:
        pac.printDetailInfo()

    elif cmdline.file_info:
        file = pac.getFileById(cmdline.file_info)
        if file is not None:
            print("          id    offset       size  compress  size  filename")
            file.printDetailInfo()

    elif cmdline.extract_id:
        with open(filename, "rb") as binfile:
            idlist = map(int, cmdline.extract_id.split(","))
            if cmdline.raw:
                location = datastruct.adjustSeparatorForFS("raw-extract/")
                if cmdline.extract:
                    location = cmdline.extract
                for fid in idlist:
                    pac.dumpFileId(fid, location, binfile)
            else:
                location = datastruct.adjustSeparatorForFS("extract/")
                if cmdline.extract:
                    location = cmdline.extract
                for fid in idlist:
                    pac.extractFileId(fid, location, binfile, debuggy=cmdline.debug)

    elif cmdline.extract:
        threads = Broker(len(pac.files))
        for fid in range(len(pac.files)):
            threads.appendNfire(extractJob, (pac, fid, cmdline, filename))
        threads.stop()
        print("Extraction job completed")

def main(cmdline):
    sekai = fileadding_utils.staging()
    docompress = not cmdline.no_compress
    dryrun = cmdline.dry_run
    # staging operations
    if cmdline.stage:
        if cmdline.add:
            if os.path.isfile(cmdline.file):
                if os.path.isdir(cmdline.base_dir):
                    relpath = os.path.relpath(cmdline.file, cmdline.base_dir)
                    newbie = sekai.addfile(relpath, cmdline.file, compression=docompress)
                    if newbie:
                        print("Added new file with name: " + datastruct.adjustSeparatorForPac(relpath))
                    else:
                        print("File " + datastruct.adjustSeparatorForPac(relpath) + " will be replaced")
                else:
                    print("directory \"" + cmdline.add + "\" si not valid")
            else:
                print("file \"" + cmdline.file + "\" not found")
            sekai.saveEnviron()
        elif cmdline.merge:
            if os.path.isdir(cmdline.file):
                sekai.addDirectory(cmdline.file, compression=docompress, verbose=True)
            else:
                print("directory \"" + cmdline.add + "\" si not valid")
            sekai.saveEnviron()
        elif cmdline.undo:
            undid = sekai.undoFile(cmdline.file)
            if not undid:
                print("Warning: command had no effect (typo in filename?)")
            sekai.saveEnviron()
        elif cmdline.remove:
            removed = sekai.removeFile(cmdline.file)
            if not removed:
                print("Warning: command had no effect (typo in filename?)")
            sekai.saveEnviron()
        elif cmdline.commit:
            sekai.commit()
            print("Commit completed")
            sekai.saveEnviron()
        elif cmdline.write:
            sekai.writeout(cmdline.file, dry_run=dryrun, debuggy=cmdline.debug)
        elif cmdline.peek:
            nonStaging(sekai.package, cmdline, sekai.target)
        elif cmdline.list:
            sekai.listInfo()

        # other operations

        elif cmdline.file: # targeting (initialize staging)
            sekai.loadPackage(cmdline.file)
            print("Staging environment initialized with target pacfile: " + sekai.target)
            sekai.saveEnviron()

        else:
            sekai.saveEnviron()

    # non-staging operations
    elif cmdline.file is not None:
        pac = datastruct.pacfile()
        with open(cmdline.file, "rb") as binfile:
            pac.loadFromFile(binfile)
        nonStaging(pac, cmdline, cmdline.file)


if __name__ == '__main__':
    commandline = cliparse.parsecli()
    main(commandline)