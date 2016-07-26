import struct,os
from ovsylib import datamover, compression, customsort
import math
import platform
from operator import attrgetter

intsize = 2
longsize = 4

"""
    This module contains classes representing the various data structures
    contained in the .pac file.
    The classes are "smart", since they contain both the data and the methods to
    read/write/manipulate it
"""


def getString(binfile, length):
    """
    Read an ascii string from a binary file; the seek is updated accordingly

    :param binfile: file object
    :param length: number of bytes
    :return: ascii string
    """
    ret = ""
    read = 0
    for i in range(length):
        char = struct.unpack("B", binfile.read(1))[0]
        if char != 0:
            ret = ret + chr(char)
        else:
            read = i + 1
            break
    if read < length:
        binfile.seek(length - read, 1)
    return ret

def outString(binfile, length, text):
    """
    Writes an ascii string to a file

    :param binfile: file object
    :param length: number of bytes
    :param text: ascii string
    """
    for i in range(length):
        if i < len(text):
            binfile.write(struct.pack("c", text[i].encode("ascii")))
        else:
            binfile.write(struct.pack("B", 0))

def adjustSeparatorForPac(originstring):
    """
    convert a string cointaining "/" path separators (i.e. unix filname)
    to a string containing "\" path separators (as used by the .pac file directory)
    """
    return originstring.replace("/","\\")

def adjustSeparatorForFS(originstring):
    """
    convert a string containing "\" path separators (as used by the .pac file directory)
    to a string containing the os specific path separator
    """
    if platform.system() == "Windows":
        return originstring.replace("/","\\")
    else:
        return originstring.replace("\\","/")


class Header:

    """
    .pac file header
    """

    def __init__(self):
        self.nfiles = 0
        self.dwpack = ""

    def load_metadata(self, binfile):
        self.dwpack = getString(binfile, 8)
        data = struct.unpack("III", binfile.read(longsize * 3))
        self.nfiles = data[1]

    def write_metadata(self, binfile, dry_run=False):
        if not dry_run:
            outString(binfile, 8, self.dwpack)
            binfile.write(struct.pack("I", 0))
            binfile.write(struct.pack("I", self.nfiles))
            binfile.write(struct.pack("I", 0))

    def print_info(self):
        print("  header (%s) File count: %d" % (self.dwpack, self.nfiles))


class FileEntry:

    def __init__(self):
        self.id = 0
        self.name = ""
        self.size = 0  # un-compressed (full) data size in byte
        self.offset = 0  # absolute offset of the data inside the .pac file.
        self.compressed = False
        self.compr_object = None  # object handling compression, assigned if needed
        self.comp_size = 0  # compressd data size in bytes
        self.import_from = ""  # if empty, it means we're writing to a new .pac file
        self.origin_offset = None  # (same as self.offset) used to read data from those entries which are copied from an existing .pac
        self.offset_writeback_location = 0

    def load_metadata(self, binfile):
        """
        Read the file metadata, update the seek accordingly
        :param binfile: file object
        :return:
        """
        data = struct.unpack("II", binfile.read(longsize * 2))
        self.id = data[1]
        self.name = getString(binfile, 260)
        data = struct.unpack("IIIII", binfile.read(longsize * 5))
        self.comp_size = data[1]
        self.size = data[2]
        if data[3] != 0:
            self.compressed = True
        self.offset = data[4]   # note: the offset read here is relative to the beginning of the data area

    def load_compression_info(self, binfile):
        """
        Initialize compr_object, the needed info are located in the data area, seek is not preserved
        :param binfile: file object
        :return:
        """
        binfile.seek(self.offset)
        self.compr_object = compression.Chuunicomp()
        try:
            self.compr_object.fromBinfile(binfile)
        except compression.BadMagicNum as e:
            print("Warning: bad magic sequence (%x) in file %s" % (int(str(e)), self.name))

    def create_from_file(self, name, filepath, compress=True, adjust_separator=True):
        """
        Prepare the FileEntry to receive data from an on-disk file to be packed
        :param name: filename used in the .pac directory
        :param filepath: path of the file to be imported
        :param compress:
        :param adjust_separator:
        :return:
        """
        if adjust_separator:
            self.name = adjustSeparatorForPac(name)
        else:
            self.name = name
        self.size = os.path.getsize(filepath)
        self.import_from = filepath
        if compress > 0:
            self.compressed = True
            self.compr_object = compression.Chuunicomp()
            chunknum = max(1, int(math.ceil(self.size / self.compr_object.default_chunksize)))
            self.compr_object.fromFutureImport(chunknum)

    def _dump2file(self, fromfile, tofile):
        actual_len = self.size
        if self.compressed:
            actual_len = self.comp_size
        datamover.dd(fromfile, tofile, self.offset, actual_len)

    def dump_myself(self, location, binfile):
        """
        Write data to a path on disk, never uncompress
        :param location: file path string
        :param binfile: file object
        :return:
        """
        print("Dumping %s to %s" % (self.name, location))
        with open(location, "wb") as savefile:
            self._dump2file(binfile, savefile)

    def extract_myself(self, location, binfile, debuggy=False):
        """
        Write data to a path on disk, uncompress if needed
        :param location: file path string
        :param binfile: file object
        :param debuggy:
        :return:
        """
        print("Extracting %s to %s" % (self.name, location))
        with open(location, "wb") as savefile:
            if self.compressed:
                binfile.seek(self.offset, 0)
                self.compr_object.decompress(binfile, savefile, debuggy=debuggy)
            else:
                self._dump2file(binfile, savefile)

    def write_out_metadata(self, updated, dry_run=False):
        """
        Write a copy of the metadata to a file
        :param updated: file object
        :param dry_run:
        :return:
        """
        if not dry_run:
            updated.write(struct.pack("I", 0))
            updated.write(struct.pack("I", self.id))
            outString(updated, 260, self.name)
            updated.write(struct.pack("I", 0))
        if self.compressed:
            self.compr_object.aftercompress_callback_obj = compression.after_comp_callback(updated.tell(), updated)
        if not dry_run:
            updated.write(struct.pack("I", self.comp_size))
            updated.write(struct.pack("I", self.size))
            compa = 0
            if self.compressed:
                compa = 1
            updated.write(struct.pack("I", compa))
            self.offset_writeback_location = updated.tell()  # save the
            updated.write(struct.pack("I", self.offset))

    def write_out_data(self, original, updated, metadata_offset, dry_run=False, debuggy=False):
        """
        Write a copy of the data to a file
        :param original: file object
        :param updated: file object
        :param metadata_offset:
        :param dry_run:
        :param debuggy:
        :return:
        """
        def writeback_offset():
            begin_data_pos = updated.tell()
            self.offset = begin_data_pos
            updated.seek(self.offset_writeback_location, 0)
            if not dry_run:
                updated.write(struct.pack("I", self.offset - metadata_offset))
            updated.seek(begin_data_pos, 0)

        if self.import_from != "":
            """ if is a new file, compress it and write the result to the .pac
            we didn't know the offset yet, so we must make a step back and fix this"""
            writeback_offset()

            if self.compressed:
                print("Compressing %s (%d chunks) ..." % (self.name, self.compr_object.chunk_num), end="\r")
                self.comp_size = self.compr_object.compress(self.import_from, updated, dry_run=dry_run, debuggy=debuggy)
                print("Compressed %s : %d -> %d (%f)" %
                      (self.name, self.size, self.comp_size, ((self.size - self.comp_size)*100) / self.size))
            else:  # uncompressed file: copy it byte by byte
                if not dry_run:
                    with open(self.import_from, "rb") as importfile:
                        datamover.dd(importfile, updated, 0, self.size)
        else:
            """ write back the file unchanged
            we rewrit the offset, since the size of some file inbetween may have changed"""
            writeback_offset()

            if not dry_run:
                actual_len = self.size
                if self.compressed:
                    actual_len = self.comp_size
                datamover.dd(original, updated, self.origin_offset, actual_len)

    def adjust_offset(self, addendum):
        """
        Called by the code utilizing this class to adjust the offset value
        :param addendum: integer
        :return:
        """
        if self.origin_offset is None:
            self.origin_offset = self.offset + addendum  # "save" the original offset, to retrieve the data
        self.offset = self.offset + addendum

    def print_info(self):
        comprs = " no"
        if self.compressed:
            comprs = "yes"
        print("   file #%03d  %08x %10d  %s %10d  %s" %
              (self.id, self.offset, self.size, comprs, self.comp_size, self.name))

    def print_detailed_info(self):
        self.print_info()
        if self.compr_object is not None:
            self.compr_object.print_info()


class Pacfile:

    def __init__(self):
        self.files = []
        self.header = Header()
        self.metadata_offset = 0

    def load_from_file(self, binfile):
        """
        Initialize the object, taking data from an existing file; after the function terminates, the seek location
        is unspecified.
        :param binfile: file object
        :return:
        """
        self.header.load_metadata(binfile)
        self.load_file_dir_entries(binfile)
        self.metadata_offset = binfile.tell()
        self.adjust_metaoff_displace()
        self.load_compression_info(binfile)

    def load_file_dir_entries(self, binfile):
        """
        Create FileEntry objects, by reading the pacfile directory data; the seek is updated accordingly
        :param binfile: file object
        :return:
        """
        for i in range(self.header.nfiles):
            newfile = FileEntry()
            newfile.load_metadata(binfile)
            self.files.append(newfile)

    def theorize_metadata_offset(self):
        """ :return: metadata offset calculated from the current number of files """
        return len(self.files) * ((7 * longsize) + 260) + (longsize * 3 + 8)

    def adjust_metaoff_displace(self, direction=1):
        """
        we need to adjust the file offset, to make it absolute inside the file
        """
        for f in self.files:
            f.adjust_offset(self.metadata_offset * direction)

    def rollback_metaoff_displace(self):
        """
        applies adjust_metaoff_displace in reverse
        """
        self.adjust_metaoff_displace(direction=-1)

    def load_compression_info(self, binfile):
        """
        For each file in the directory, ask it to load its compression info.
        After the function terminates, the seek location is unspecified
        :param binfile: file object
        :return:
        """
        for f in self.files:
            if f.compressed:
                f.load_compression_info(binfile)

    def getFileById(self, fid):
        for f in self.files:
            if f.id == fid:
                return f
        return None

    def listFileIDs(self):
        ids = []
        for f in self.files:
            ids.append(f.id)
        return ids

    def listFileNames(self):
        return map(attrgetter("name"), self.files)

    def create_destination(self, fid, destination):
        """
        :param fid: file id (integer)
        :param destination: file path string
        :return:
        """
        file = self.getFileById(fid)
        fname = adjustSeparatorForFS(file.name)
        fullpath = os.path.join(os.getcwd(), os.path.join(destination, fname))
        os.makedirs(os.path.dirname(fullpath), exist_ok=True)
        return fullpath

    def dumpFileId(self, fid, destination, binfile):
        """ do not decompress extracted file."""
        file = self.getFileById(fid)
        fullpath = self.create_destination(fid, destination)
        file.dumpMyself(fullpath, binfile)

    def extractFileId(self, fid, destination, binfile, debuggy=False):
        """ it's the actual file to decide if run decompres, based on metadata """
        file = self.getFileById(fid)
        fullpath = self.create_destination(fid, destination)
        file.extractMyself(fullpath, binfile, debuggy=debuggy)

    def append_file(self, file, start_id=0):
        """
        Add a new file to (the bottom of) the file list contained in this object.
        All the offsets are also re-calculated
        """
        self.rollback_metaoff_displace()
        if len(self.files) > 0:
            file.id = max(self.listFileIDs()) + 1
        else:
            file.id = start_id
        self.files.append(file)
        self.header.nfiles += 1
        self.metadata_offset = self.theorize_metadata_offset()
        self.adjust_metaoff_displace()

    def remove_file(self, file):
        """
        Remove a file from the file list contained in this object.
        All the offsets are also re-calculated
        """
        if file in self.files:
            self.rollback_metaoff_displace()
            self.files.remove(file)
            self.header.nfiles -= 1
            self.metadata_offset = self.theorize_metadata_offset()
            self.adjust_metaoff_displace()
            self.refreshFileIDs()

    def refreshFileIDs(self, start_id=0):
        for file in self.files:
            file.id = self.files.index(file) + start_id  # make sure ids are still consistent

    def sortFiles(self, start_id=0):
        self.files = sorted(self.files, key=customsort.cmp_to_key(customsort.asciicompare))
        self.refreshFileIDs(start_id=start_id)

    def preWriteFixHeader(self):
        """
        Invoked by the code making use of this class, if it has intention
        to write a fully new pacfile
        """
        if self.header.nfiles != len(self.files):
            self.header.nfiles = len(self.files)
        if self.header.dwpack != "DW_PACK":
            self.header.dwpack = "DW_PACK"

    def createCopy(self, original, filename, dry_run=False, debuggy=False, progresscback=None, abort=None):
        """
        :param original: file object
        :param filename: file object
        :param dry_run:
        :param debuggy:
        :param progresscback:
        :param abort:
        :return:
        """
        with open(filename, "wb") as updatedversion:
            self.header.write_metadata(updatedversion, dry_run=dry_run)
            for file in self.files:
                file.write_out_metadata(updatedversion, dry_run=dry_run)
            for file in self.files:
                file.write_out_data(original, updatedversion, self.metadata_offset, dry_run=dry_run, debuggy=debuggy)
                if progresscback is not None:
                    progresscback(file)
                if abort is not None:
                    if abort():
                        break

    def searchFile(self, name, exact_match=True, adjust_separator=True):
        """ :return: list of file ids """
        ret = []
        if adjust_separator:
            name = adjustSeparatorForPac(name)
        for file in self.files:
            if exact_match:
                if file.name == name:
                    ret.append(file.id)
            else:
                if file.name.startswith(name):
                    ret.append(file.id)
        return ret

    def print_info(self):
        print("Metadata size: %06x" % (self.metadata_offset,))
        self.header.print_info()
        print("          id    offset       size  compress  size  filename")
        for file in self.files:
            file.print_info()

    def print_detailed_info(self):
        print("Metadata size: %06x" % (self.metadata_offset,))
        self.header.print_info()
        print("          id    offset       size  compress  size  filename")
        for file in self.files:
            file.print_detailed_info()

