import bitarray
import struct
import math

"""
compression algorith based on the following structure:
Note: the data structures aren't aligned at all, meaning we'll have to parse it bit by bit.
([algo1 header] actually handled elsewhere, this code deals with data starting in the next area)
[vectorized tree]
[compressed data]


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
        self.childzero = None   # if I'm ever getting children, I'll name them like this
        self.childone = None
        self.isleaf = False     # to let the algorithm know when to stop
        self.isActive = True    # active node: a subtree can be attached here
        self.value = b"\0"       # value (a single byte)

    def setValue(self, value):
        self.isActive = False
        self.isleaf = True
        self.value = value

    def expandNode(self):
        """ append a left (zero) and right (one) child, left is returned """
        return self.bilateralExpand()[0]

    def bilateralExpand(self):
        self.isActive = False
        self.isleaf = False
        self.childzero = TreeNode()
        self.childone = TreeNode()
        return [self.childzero, self.childone]

    def findFirstActive(self):
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
        worknode = root.findFirstActive()
        if worknode is None:  # if the tree is completely built, then stop
            break
        # read the 'spacers'
        downleft_distance = 0
        while bitstream[cursor] != False:
            downleft_distance += 1
            cursor += 1
        cursor += 1
        # read the byte
        value = bitstream[cursor:cursor+8].tobytes()
        cursor += 8
        for i in range(downleft_distance):
            worknode = worknode.expandNode()
        worknode.setValue(value)
    return root, cursor

def uncompress(binfile, destfile, numbytes, bytes_out, debuggy=False):
    bitstream = bitarray.bitarray(endian="big")
    bitstream.frombytes(binfile.read(numbytes))

    cursor = 0
    root = TreeNode()
    bytes_written = 0

    root, cursor = buildtree(root, cursor, bitstream)

    if debuggy:
        print("Tree parsing finished: cursor at HEADER + %x, bit #%d" % (math.floor(cursor/8), cursor % 8))
        tree2dot(root, "debugtree.dot")

    while bytes_written < bytes_out:
        tarzan = root
        while not tarzan.isleaf:
            try:
                chu = bitstream[cursor]
            except IndexError:
                print("Data parsing aborted: end of bitstream (%d/%d bytes written)"
                      % (bytes_written, bytes_out))
                return
            cursor += 1
            if chu == False:
                tarzan = tarzan.childzero
            else:
                tarzan = tarzan.childone
        destfile.write(tarzan.value)
        bytes_written += 1

def collectBytes(Lb, multib, sourcefile):
    sourcefile.seek(0, 0)
    readbyte = sourcefile.read(1)
    while readbyte:
        if readbyte not in Lb:
            Lb.append(readbyte)
            multib[readbyte] = 1
        else:
            multib[readbyte] += 1
        readbyte = sourcefile.read(1)

def evalCost(num, Lb, multib, offset, depth):
    sum = 0
    for pos in range(offset, offset + num):
        sum += multib[Lb[pos]] * depth
    return sum

def clamp(bot, top, n):
    return max(bot, min(n, top))

def recursiveBest(Lb, multib, offset, depth):
    best_cost = 9999999999999
    best_num = 0
    #print("enrty level, len(Lb)=%d, offset=%d" % (len(Lb), offset))
    for i in range(math.ceil(math.log2(len(Lb)))):
        p = 2**i
        if p <= len(Lb) - offset:
            #print("%d: trying p=%d" % (depth, p))
            evcost = evalCost(p, Lb, multib, offset, depth)
            if evcost >= best_cost:
                continue
            if len(Lb) - p - offset > 0:
                #print("%d: stepping in" % (depth))
                recur_num, recur_cost = recursiveBest(Lb, multib, offset + p, depth + 1)
                #print("%d: recur_cost=%d" % (depth, recur_cost))
            else:
                recur_cost = 0
            cost = evcost + recur_cost
            if cost < best_cost:
                best_cost = cost
                best_num = p
    print("depth: %d, local optimum (%d): %s" % (depth, best_num, ".".join(map(str, Lb[offset:offset+best_num]))))
    return best_num, best_cost # bestnum, bestcost

def appendCluster(node, breadth):
    """ :return: list of children nodes """
    worklist = [node]
    for i in range(round(math.log2(breadth))):
        toappend = []
        for delenda in worklist:
            toappend.extend(delenda.bilateralExpand())
        worklist = toappend
    return worklist

def buildOptimumTree(sourcefile):
    Lb = []
    multib = {}
    def keyfun(elem):
        return multib[elem]
    root = TreeNode()
    collectBytes(Lb, multib, sourcefile)
    print("variety: %d" % len(Lb))
    Lb = sorted(Lb, key=keyfun, reverse=True)
    active_node = root
    while len(Lb) > 0:
        n_pick, n_cost = recursiveBest(Lb, multib, 0, 1)
        print("picked: %d" % n_pick)
        # append first n_pick nodes to the left subtree
        if n_pick > 0:
            active_node.bilateralExpand()
            cluster = appendCluster(active_node.childzero, n_pick)
            for i in range(n_pick):
                cluster[i].setValue(Lb[i])
            # right node becomes active
            active_node = active_node.childone
        else:
            active_node.setValue(Lb[0])
            Lb.pop(0)
        # remove n_pick nodes from Lb
        for i in range(n_pick):
            Lb.pop(0)
    return

def buildpercentb(Lb, multib, percentb):
    total = 0
    for k,v in multib.items():
        total += v
    for k,v in multib.items():
        percentb[k] = float(v / total)

def buildOkTree(sourcefile):
    Lb = []
    multib = {}
    percentb = {}
    def keyfun(elem):
        return multib[elem]
    def pocketsum(elems):
        summa = 0.0
        for e in elems:
            summa += percentb[e]
        return summa
    root = TreeNode()
    collectBytes(Lb, multib, sourcefile)
    buildpercentb(Lb, multib, percentb)
    Lb = sorted(Lb, key=keyfun, reverse=True)
    active_node = root
    target_percent = 0.5
    while len(Lb) > 0:
        subspace = 0
        for space in range(len(Lb)):
            subspace = Lb[0:space+1]
            if pocketsum(subspace) >= target_percent:
                break
        target_p2 = clamp(1, 2**math.floor(math.log2(len(Lb))), 2**math.ceil(math.log2(len(subspace))))

        if len(Lb) - target_p2 > 0:
            active_node.bilateralExpand()
            cluster = appendCluster(active_node.childzero, target_p2)
        else:
            cluster = appendCluster(active_node, target_p2)
        for i in range(target_p2):
            cluster[i].setValue(Lb[i])
        active_node = active_node.childone

        for i in range(target_p2):
            Lb.pop(0)

        target_percent = target_percent / 2

    return root

def compress(sourcefile, destfile, dry_run=False, debuggy=False):
    """ :return: number of bytes written """
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

    tree = buildOkTree(sourcefile)
    sourcefile.seek(0)

    if debuggy:
        tree2dot(tree, "optimumtree.dot")

    build_vector_tree(tree)

    datum = sourcefile.read(1)
    while datum:
        if datum not in lookup_table.keys():
            build_lookup_table(tree, bitarray.bitarray(endian="big"), datum)
        out_bitstream.extend(lookup_table[datum])
        datum = sourcefile.read(1)

    destfile.write(out_bitstream.tobytes())

    print("compression, done")
    return out_bitstream.buffer_info()[1]  # length in bytes (I hope)
