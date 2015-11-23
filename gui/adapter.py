import sys,os

def listToTree(pathlist, separator="\\"):
    data = []

    def getElement(root, key):
        ret = None
        for sub in root[1]:
            if sub[0] == key:
                ret = sub
        return ret

    def getLabel(elem):
        return elem[0]

    def getChildren(elem):
        return elem[1]

    for elem in pathlist:
        pieces = elem.split(separator)
        for i in range(len(pieces)):
            if i == 0:
                if pieces[i] not in map(getLabel, data):
                    data.append((pieces[i], []))
            else:
                current = ("", data)
                for j in range(i):
                    current = getElement(current, pieces[j])
                if pieces[i] not in map(getLabel, getChildren(current)):
                    current[1].append((pieces[i], []))

    return data

def getHome():
    if sys.platform.startswith('linux'):
        return os.getenv("HOME")
    else:
        return os.getenv("HOMEPATH")