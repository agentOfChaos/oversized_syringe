from math import ceil


def read_file_chunk(file, chunk_size=1024):
    while True:
        block = file.read(chunk_size)
        if not block:
            break
        yield block

def dd(iffy, vert, offset, length, blocksize=1024):
    """

    :param iffy: input file
    :param vert: output file
    """
    compa = ceil(length / blocksize)
    iffy.seek(offset, 0)
    for i in range(compa):
        data = next(read_file_chunk(iffy, blocksize))
        if i == compa - 1:
            falcom = length % blocksize
            data = data[:falcom]
        vert.write(data)
