import bitarray
import struct
import math

"""
compression algorithm based on the following structure:
Note: the data structures aren't aligned at all, meaning we'll have to parse it bit by bit.
([algo1 header] actually handled elsewhere, this code deals with data starting in the next area)
[vectorized tree]
[compressed data]
Basically, it employs Huffman coding. I called it Yggdrasil because I didn't know about HC yet,
but I knew data structures.

vectorialized tree structure:

A sequence of units looks like this:
[spacer][payload byte]
I like to call it 'spacer' because of historical reasons, since for some of the re-eng time those
little fellas where a complete mistery.
The spacer is a sequence of bit like this: 1*0 (* is the kleene star, duh)
The payload byte is an actual data byte, in uncompressed form

The tree is built like this:
1) Initialize the tree with a root node
2) The root node is the leftmost active node
3) Repeat until the tree is fully populated:
    a) Select the leftmost active node (the one which is not a leaf, but has no children yet)
    b) The number of '1's in the spacer tells us how many expansions to do (add 2 non-leaf children to the active node);
       the drill is: expand one, the leftmost becomes the active node, repeat until all the expansions are done
    c) If the expansions are done (0 expansions is possible), turn the current active node into a leaf,
       its value is specified in the 8 bits following the spacer

After the tree is built, the compressed data starts right away
A unit of data looks like this:
[one or more 'navigator bits']

The data is parsed like this:
Repeat until length(written data) == uncompressed value specified in header
    1) current working node (I like to call it 'tarzan') := tree's root
    2) repeat while the working node is not a leaf node:
        a) read one navigator bit
        b) if the bit is 0, then update working node := current working node's left child
        c) if the bit is 1, then update working node := current working node's right child
    3) write out the current working node's value (a byte)
    4) increment written_data , repeat
"""


class TreeNode:

    def __init__(self):
        self.childzero = None   # if I'm ever having children, I'll name them like this
        self.childone = None
        self.isleaf = False     # to let the algorithm know when to stop
        self.isActive = True    # active node: a subtree can be attached here
        self.value = b"\0"       # value (a single byte)

    def set_value(self, value):
        self.isActive = False
        self.isleaf = True
        self.value = value

    def expand_node(self):
        """ append a left (zero) and right (one) child, left is returned """
        return self.bilateral_expand()[0]

    def bilateral_expand(self):
        """ append a left (zero) and right (one) child, return a list containing both """
        self.isActive = False
        self.isleaf = False
        self.childzero = TreeNode()
        self.childone = TreeNode()
        return [self.childzero, self.childone]

    def find_first_active(self):
        """ recursive depth-first search for the leftmost active node """
        if self.isleaf:
            return None
        if self.isActive:
            return self
        if self.childzero.isActive:
            return self.childzero
        deepleft = self.childzero.findFirstActive()
        if deepleft is not None:
            return deepleft
        if self.childone.isActive:
            return self.childone
        deepright = self.childone.findFirstActive()
        if deepright is not None:
            return deepright
        return None


def tree2dot(root, filename):
    seen_nodes = []

    def traversal(node):
        seen_nodes.append(node)
        if not node.isleaf:
            traversal(node.childzero)
            traversal(node.childone)

    traversal(root)
    with open(filename, "w") as tfile:
        tfile.write("digraph yggdrasil {\n")
        for node in seen_nodes:
            tfile.write("node_" + str(seen_nodes.index(node)))
            if node.isleaf:
                tfile.write(" [label=\"%x\"]" % struct.unpack("B", node.value))
            else:
                tfile.write(" [label=\"\"]")
            tfile.write("\n")
        for node in seen_nodes:
            if not node.isleaf:
                tfile.write("node_" + str(seen_nodes.index(node)) + " -> node_" + str(seen_nodes.index(node.childzero)) +
                            " [label=0]\n")
                tfile.write("node_" + str(seen_nodes.index(node)) + " -> node_" + str(seen_nodes.index(node.childone)) +
                            " [label=1]\n")
        tfile.write("}\n")


def buildtree(root, cursor, bitstream):
    while True:
        # get the active node to work on
        worknode = root.find_first_active()
        if worknode is None:  # if the tree is completely built, then stop
            break
        # read the 'spacers'
        downleft_distance = 0
        try:
            while bitstream[cursor]:
                downleft_distance += 1
                cursor += 1
        except IndexError:
            print("Tree parsing aborted: cursor at HEADER + %x, bit #%d" % (math.floor(cursor/8), cursor % 8))
            return None, None
        cursor += 1
        # read the byte
        value = bitstream[cursor:cursor+8].tobytes()
        cursor += 8
        for i in range(downleft_distance):
            worknode = worknode.expand_node()
        worknode.set_value(value)
    return root, cursor

def uncompress(binfile, destfile, numbytes, bytes_out, debuggy=False):
    bitstream = bitarray.bitarray(endian="big")
    bitstream.frombytes(binfile.read(numbytes))
    cursor = 0
    root = TreeNode()
    bytes_written = 0

    root, cursor = buildtree(root, cursor, bitstream)
    if root is None:
        print("Tree construction failed, exiting")
        return

    if debuggy:
        print("Tree parsing finished: cursor at %x, bit #%d" % (math.floor(cursor/8), cursor % 8))
        tree2dot(root, "debugtree.dot")

    while bytes_written < bytes_out:
        tarzan = root
        while not tarzan.isleaf:
            try:
                chu = bitstream[cursor]
            except IndexError:
                print("Data parsing aborted: end of bitstream, cursor at %x, bit #%d (%d/%d bytes written)"
                      % (math.floor(cursor/8), cursor % 8, bytes_written, bytes_out))
                return
            cursor += 1
            if chu == False:
                tarzan = tarzan.childzero
            else:
                tarzan = tarzan.childone
        destfile.write(tarzan.value)
        bytes_written += 1

def collectBytes(Lb, multib, sourcefile, start_offs, end_offs):
    sourcefile.seek(start_offs, 0)
    readbyte = sourcefile.read(1)
    target_read = 0
    while readbyte and (target_read < (end_offs - start_offs)):
        if readbyte not in Lb:
            Lb.append(readbyte)
            multib[readbyte] = 1
        else:
            multib[readbyte] += 1
        readbyte = sourcefile.read(1)
        target_read += 1


def buildHuffmanTree(sourcefile, start_offs, end_offs):
    Lb = []
    multib = {}
    nodemap = []
    def keyfun(elem):
        return multib[elem]
    collectBytes(Lb, multib, sourcefile, start_offs, end_offs)
    Lb = sorted(Lb, key=keyfun)

    for b in Lb:
        nn = TreeNode()
        nn.set_value(b)
        nodemap.append((b, nn, multib[b]))

    while len(nodemap) > 1:
        uno = nodemap.pop(0)
        due = nodemap.pop(0)
        radix = TreeNode()
        radix.childzero = uno[1]
        radix.childone = due[1]
        newcost = uno[2] + due[2]
        i = 0
        while i < len(nodemap):
            if nodemap[i][2] > newcost:
                break
            i += 1
        nodemap.insert(i, (0, radix, newcost))

    return nodemap[0][1]


def compress(sourcefile, start_offs, end_offs, debuggy=False):
    """ :return: bitarray object containing the compressed data """
    lookup_table = {}
    vecbuild_path = bitarray.bitarray(endian="big")
    out_bitstream = bitarray.bitarray(endian="big")

    def build_lookup_table(node, path, search):
        if not node.isleaf:
            lefty = path.copy()
            lefty.append(False)
            righty = path.copy()
            righty.append(True)
            build_lookup_table(node.childzero, lefty, search)
            build_lookup_table(node.childone, righty, search)
        elif node.value == search:
            lookup_table[search] = path

    def build_vector_tree(node):
        if node.isleaf:
            vecbuild_path.append(False)
            out_bitstream.extend(vecbuild_path)
            for i in range(len(vecbuild_path)): vecbuild_path.pop()
            val = bitarray.bitarray(endian="big")
            val.frombytes(node.value)
            out_bitstream.extend(val)
        else:
            vecbuild_path.append(True)
            build_vector_tree(node.childzero)
            build_vector_tree(node.childone)

    tree = buildHuffmanTree(sourcefile, start_offs, end_offs)
    sourcefile.seek(start_offs)

    if debuggy:
        tree2dot(tree, "optimumtree.dot")

    build_vector_tree(tree)

    datum = sourcefile.read(1)
    target_read = 0
    while datum and (target_read < (end_offs - start_offs)):
        if datum not in lookup_table.keys():
            build_lookup_table(tree, bitarray.bitarray(endian="big"), datum)
        out_bitstream.extend(lookup_table[datum])
        datum = sourcefile.read(1)
        target_read += 1

    return out_bitstream
