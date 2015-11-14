import struct
import os
from ovsylib.compresion_algos import yggdrasil

intsize = 4


def checksize(binfile):
    old_file_position = binfile.tell()
    binfile.seek(0, os.SEEK_END)
    size = binfile.tell()
    binfile.seek(old_file_position, os.SEEK_SET)
    return size


class algo1:

    def __init__(self):
        self.uncomp_size = 0
        self.comp_size = 0
        self.rootaddress = 0
        self.header_write_back_offset = 0

    def loadSubHeaderFromFile(self, binfile):
        self.uncomp_size = struct.unpack("I", binfile.read(intsize))[0]
        self.comp_size = struct.unpack("I", binfile.read(intsize))[0]
        self.rootaddress = struct.unpack("I", binfile.read(intsize))[0]

    def decompress(self, binfile, metadata_offset, savefile, debuggy=False):
        binfile.seek(metadata_offset + self.rootaddress, 0)
        yggdrasil.uncompress(binfile, savefile, self.comp_size, self.uncomp_size, debuggy=debuggy)

    def writeSubHeader(self, savefile, dry_run=False):
        self.header_write_back_offset = savefile.tell()
        if not dry_run:
            savefile.write(struct.pack("I", self.uncomp_size))
            savefile.write(struct.pack("I", self.comp_size))
            savefile.write(struct.pack("I", self.rootaddress))

    def compress(self, sourcefile, savefile, metadata_offset, dry_run=False, debuggy=False):
        """ :return: number of compressed bytes """
        bytes_uncomp = checksize(sourcefile)
        self.uncomp_size = bytes_uncomp
        self.rootaddress = savefile.tell() - metadata_offset
        bytes_out = yggdrasil.compress(sourcefile, savefile, dry_run=dry_run, debuggy=debuggy)
        afterwrite_offset = savefile.tell()

        # now re-create a fresh sub header
        self.comp_size = bytes_out

        savefile.seek(self.header_write_back_offset, 0)
        self.writeSubHeader(savefile, dry_run=dry_run)
        savefile.seek(afterwrite_offset, 0)
        return self.comp_size

    def printInfo(self):
        print("partial comp size: %d ; partial uncomp size: %d ; relative root address: %x"
              % (self.comp_size, self.uncomp_size, self.rootaddress))


class after_comp_callback:

    def __init__(self, address, binfile):
        self.address = address
        self.binfile = binfile

    def compressed(self, length, dry_run=False):
        savedpos = self.binfile.tell()
        self.binfile.seek(self.address, 0)
        if not dry_run:
            self.binfile.write(struct.pack("I", length))
        self.binfile.seek(savedpos, 0)


class chuunicomp:

    chunksize = 0x20000

    def __init__(self):
        self.magicseq = 0
        self.chunk_num = 0
        self.const2 = 0
        self.header_size = 0
        self.chunks = []
        self.aftercompress_callback_obj = None

    def fromBinfile(self, binfile):
        self.magicseq = struct.unpack("I", binfile.read(intsize))[0]
        if self.magicseq != 0x1234:
            print("magic sequence: %x" % self.magicseq)
        assert self.magicseq == 0x1234
        self.chunk_num = struct.unpack("I", binfile.read(intsize))[0]
        self.const2 = struct.unpack("I", binfile.read(intsize))[0]
        assert self.const2 == 0x20000
        self.header_size = struct.unpack("I", binfile.read(intsize))[0]
        self.chunks = self.prepareChunks(binfile)

    def fromFutureImport(self, chunksnum):
        self.magicseq = 0x1234
        self.chunk_num = chunksnum
        self.const2 = 0x20000
        self.chunks = self.prepareChunks(None)
        self.header_size = 4 + (3 * chunksnum)

    def prepareChunks(self, binfile=None):
        body = []
        for i in range(self.chunk_num):
            piece = algo1()
            if binfile is not None:
                piece.loadSubHeaderFromFile(binfile)
            body.append(piece)
        return body

    def decompress(self, binfile, savefile, debuggy=False):
        # we don't read the header at compression time, since we have already acquired the data
        binfile.seek(self.header_size, 1)
        metadata_offset = binfile.tell()
        for chunk in self.chunks:
            chunk.decompress(binfile, metadata_offset, savefile, debuggy=debuggy)

    def writeHeader(self, savefile, dry_run=False):
        if not dry_run:
            savefile.write(struct.pack("I", self.magicseq))
            savefile.write(struct.pack("I", self.chunk_num))
            savefile.write(struct.pack("I", self.const2))
            savefile.write(struct.pack("I", self.header_size))

    def compress(self, sourcefile, savefile, dry_run=False, debuggy=False):
        totalcomp = 0
        self.writeHeader(savefile, dry_run=dry_run)
        for chunk in self.chunks:
            chunk.writeSubHeader(savefile, dry_run=dry_run)
        for chunk in self.chunks:
            totalcomp += chunk.compress(sourcefile, savefile, self.header_size, dry_run=dry_run, debuggy=debuggy)
        if self.aftercompress_callback_obj is not None:
            self.aftercompress_callback_obj.compressed(totalcomp + self.header_size, dry_run=dry_run)

    def printInfo(self):
        print("     Compression type: %02d , header size: %04x" % (self.chunk_num, self.header_size))
        for chunk in self.chunks:
            print("     chunk #%03d: " % (self.chunks.index(chunk),), end="")
            chunk.printInfo()