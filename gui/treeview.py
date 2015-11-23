import os

from PyQt4 import QtGui

def splitpath(path):
    folders = []
    while True:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        else:
            if path != "":
                folders.append(path)

            break

    folders.reverse()
    return folders

class CoolTreeView(QtGui.QTreeView):

    def expand_path(self, path):
        folders = splitpath(path)
        for i in range(1, len(folders) + 1):
            current = os.path.join(folders[0], *folders[1:i])
            index = self.model().index(current)
            self.expand(index)
