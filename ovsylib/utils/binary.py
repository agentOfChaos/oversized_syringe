import struct


def get_string(binfile, length):
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


def put_string(binfile, length, text):
    """
    Writes an ascii string to a file

    :param binfile: file object
    :param length: number of bytes; if the string is shorter, the length is padded with 0x00 bytes
    :param text: ascii string
    """
    for i in range(length):
        if i < len(text):
            binfile.write(struct.pack("c", text[i].encode("ascii")))
        else:
            binfile.write(struct.pack("B", 0))
