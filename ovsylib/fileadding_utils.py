from ovsylib import datastruct
import os
import pickle


environ_name = ".ovs_staging"


def listrecursive(root):
    allfiles = {}
    for rootfolder, dirs, files in os.walk(root):
        for file in files:
            fullpath = os.path.join(os.path.abspath(rootfolder), file)
            allfiles[fullpath] = datastruct.adjustSeparatorForPac(os.path.relpath(fullpath, root))
    return allfiles


class staging:

    def __init__(self):
        self.package = datastruct.pacfile()
        self.target = ""
        self.deletes = []
        self.appends = []
        if os.path.isfile(environ_name):
            self.loadEnviron()

    def loadPackage(self, path):
        with open(path, "rb") as binfile:
            self.target = path
            self.package.loadFromFile(binfile)

    def addfile(self, internal_name, path, compression=True):
        collisions = self.package.searchFile(internal_name)
        if len(collisions) == 0:
            newfile = datastruct.fileentry()
            newfile.createFromFile(internal_name, path,compress=compression)
            self.appends.append(newfile)
            return True
        elif len(collisions) == 1:
            self.deletes.extend(collisions)  # stage delete old
            newfile = datastruct.fileentry()
            newfile.createFromFile(internal_name, path,compress=compression)
            self.appends.append(newfile)  # stage append new
            return False
        else:
            print("Directory consisteny error")  # cryptic error message
            pass # error

    def addDirectory(self, dirpath, verbose=False, compression=True):
        addenda = listrecursive(dirpath)
        for fs,pac in addenda.items():
            newbie = self.addfile(pac, fs, compression=compression)
            if newbie and verbose:
                print("added " + fs + " as " + pac)
            elif not newbie and verbose:
                print(fs + " will replace " + pac)

    def undoFile(self, name):
        modified = False
        for add in self.appends:
            if add.name == name:
                self.appends.remove(add)
                modified = True
        for dele in self.deletes:
            if dele.name == name:
                self.deletes.remove(dele)
                modified = True
        return modified

    def removeFile(self, name):
        modif = False
        for add in self.appends:
            if add.name == name:
                self.appends.remove(add)
                modif = True
        if name not in self.deletes:
            target = self.package.searchFile(name, exact_match=True)
            if len(target) == 1:
                self.deletes.append(target[0])
                modif = True
        return modif

    def commit(self):
        for dele in self.deletes:
            self.package.removeFile(dele)
        for add in self.appends:
            self.package.appendFile(add)
        self.package.sortFiles()
        self.deletes = []
        self.appends = []

    def writeout(self, destination, dry_run=False):
        with open(self.target, "rb") as origin:
            self.package.createCopy(origin, destination, dry_run=dry_run)
        if not dry_run:
            self.clearEnviron()

    def listInfo(self):
        print("Target: " + self.target)
        for add in self.appends:
            modif = False
            for dele in self.deletes:
                if dele.name == add.name:
                    modif = True
            if modif:
                print("modify: %s <- %s" % (add.name, add.import_from))
            else:
                print("create: %s <- %s" % (add.name, add.import_from))
        for dele in self.deletes:
            modif = False
            for add in self.appends:
                if dele.name == add.name:
                    modif = True
            if not modif:
                print("delete: %s" % (dele.name,))

    def saveEnviron(self):
        pickle.dump([self.package, self.target, self.appends, self.deletes], open(environ_name, "wb"))

    def loadEnviron(self):
        data = pickle.load(open(environ_name, "rb"))
        self.package = data[0]
        self.target = data[1]
        self.appends = data[2]
        self.deletes = data[3]

    def clearEnviron(self):
        os.remove(environ_name)
