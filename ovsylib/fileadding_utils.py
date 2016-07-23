from ovsylib import datastruct
import os
import pickle


environ_name = ".ovs_staging"

def topdir(root):
    if root[len(root) - 1] == "\\" or root[len(root) - 1] == "/":
        root = root[:-1]
    return os.path.basename(root)

def listrecursive(root, wholedir=False):
    allfiles = {}
    for rootfolder, dirs, files in os.walk(root):
        for file in files:
            fullpath = os.path.join(os.path.abspath(rootfolder), file)
            if wholedir:
                localname = os.path.join(topdir(root), os.path.relpath(fullpath, root))
            else:
                localname = os.path.relpath(fullpath, root)
            allfiles[fullpath] = datastruct.adjustSeparatorForPac(localname)
    return allfiles


class staging:

    def __init__(self):
        self.package = datastruct.Pacfile()
        self.target = ""
        self.start_id = 0
        self.deletes = []
        self.appends = []
        if os.path.isfile(environ_name):
            self.loadEnviron()
            print("Loaded staging environment from disk")

    def loadPackage(self, path):
        with open(path, "rb") as binfile:
            self.target = path
            self.package.load_from_file(binfile)
            self.start_id = min(self.package.listFileIDs())

    def addfile(self, internal_name, path, compression=True):
        collisions = self.package.searchFile(internal_name)
        if len(collisions) == 0:
            newfile = datastruct.FileEntry()
            newfile.create_from_file(internal_name, path, compress=compression)
            self.appends.append(newfile)
            return True
        elif len(collisions) == 1:
            self.deletes.append(self.package.getFileById(collisions[0]))  # stage delete old
            newfile = datastruct.FileEntry()
            newfile.create_from_file(internal_name, path, compress=compression)
            self.appends.append(newfile)  # stage append new
            return False
        else:
            print("Directory consisteny error")  # cryptic error message
            pass # error

    def addDirectory(self, dirpath, verbose=False, compression=True, wholedir=False):
        addenda = listrecursive(dirpath, wholedir=wholedir)
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
                self.deletes.append(self.package.getFileById(target[0]))
                modif = True
        return modif

    def commit(self):
        for dele in self.deletes:
            self.package.remove_file(dele)
        for add in self.appends:
            self.package.append_file(add, start_id=self.start_id)
        self.package.sortFiles(start_id=self.start_id)
        if len(self.deletes) + len(self.appends) == 0:
            print("Nothing to do")
        self.deletes = []
        self.appends = []

    def writeout(self, destination, dry_run=False, debuggy=False, progresscback=None, abort=None):
        if self.target != "":
            with open(self.target, "rb") as origin:
                self.package.createCopy(origin, destination, dry_run=dry_run, debuggy=debuggy,
                                        progresscback=progresscback, abort=abort)
        else:
            self.package.preWriteFixHeader()
            self.package.createCopy(None, destination, dry_run=dry_run, debuggy=debuggy,
                                    progresscback=progresscback, abort=abort)

    def listInfo(self):
        targstr = self.target
        if targstr == "":
            targstr = "<empty, create new>"
        print("Target: " + targstr)
        print("First element id: %d (0x%x)" % (self.start_id, self.start_id))

    def listStagedCreate(self):
        ops = []
        for add in self.appends:
            modif = False
            for dele in self.deletes:
                if dele.name == add.name:
                    modif = True
            if not modif:
                ops.append("%s <- %s" % (add.name, add.import_from))
        return ops

    def listStagedModify(self):
        ops = []
        for add in self.appends:
            modif = False
            for dele in self.deletes:
                if dele.name == add.name:
                    modif = True
            if modif:
                ops.append("%s <- %s" % (add.name, add.import_from))
        return ops

    def listStagedDelete(self):
        ops = []
        for dele in self.deletes:
            modif = False
            for add in self.appends:
                if dele.name == add.name:
                    modif = True
            if not modif:
                ops.append("%s" % (dele.name,))
        return ops

    def listDetailed(self):
        self.listInfo()
        for op in self.listStagedCreate():
            print("create: " + op)
        for op in self.listStagedModify():
            print("modify: " + op)
        for op in self.listStagedDelete():
            print("delete: " + op)

    def saveEnviron(self):
        pickle.dump([self.package, self.target, self.start_id, self.appends, self.deletes], open(environ_name, "wb"))

    def loadEnviron(self):
        data = pickle.load(open(environ_name, "rb"))
        self.package = data[0]
        self.target = data[1]
        self.start_id = data[2]
        self.appends = data[3]
        self.deletes = data[4]

    def clearEnviron(self):
        os.remove(environ_name)
