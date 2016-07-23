import os
from operator import attrgetter
from PyQt4 import QtGui, QtCore

from ovsylib.aggressive_threading import Broker


class CustomThread(QtCore.QThread):
    def __init__(self):
        super(CustomThread, self).__init__()
        self.exiting = False
        self.handbrake = False
        self.abort_interface = None

    def run(self, *args, **kwargs):
        self.target(self, *args, **kwargs)

    def abort(self):
        if self.abort_interface is not None:
            self.abort_interface.abort()

    def __del__(self):
        self.exiting = True
        self.wait()

    def progressCallback(self, file):
        self.emit(QtCore.SIGNAL("progressfile"), file)

    def errormessage(self, message):
        self.emit(QtCore.SIGNAL("errormsg"), message)


def extractJob(pac, fid, destdir, filename):
    with open(filename, "rb") as binfile:
        pac.extractFileId(fid, destdir, binfile, debuggy=False)


class GeoFront:
    def __init__(self, app):
        self.app = app
        self.working = False
        self.percent = 0
        self.doneunits = 0
        self.numunits = 1
        self.unsaved = False
        self.opname = ["idle", "idling"]
        self.worker = CustomThread()
        self.app.connect(self.worker, QtCore.SIGNAL("progressfile"), self.progressFile)
        self.app.connect(self.worker, QtCore.SIGNAL("errormsg"), app.errorbox)

    def progressFile(self, file):
        self.doneunits += 1
        self.percent = (self.doneunits * 100) / self.numunits
        self.app.updateProgress(self.percent, "%s: %s file %s" %
                                (self.opname[0], self.opname[1], file.name))

    def can_start(self):
        return not self.working

    def abort(self):
        if self.working:
            self.worker.handbrake = True
            self.worker.abort()

    def after_run(self, thread, msg):
        if thread.handbrake:
            thread.errormessage("\"%s\" operation aborted by user" % self.opname[0])
            self.app.doneCback("Interrupted; " + msg, maxoutbar=False)
        else:
            self.app.doneCback(msg)
        thread.handbrake = False
        self.working = False
        thread.abort_interface = None

    def extract(self, internalname, saveto):
        if self.can_start():
            self.opname = ["extract package", "extracting"]
            def capsule(thread):
                threads = Broker(len(self.app.staging.package.files))
                thread.abort_interface = threads
                fids = self.app.staging.package.searchFile(internalname, exact_match=False)
                for fid in fids:
                    if thread.handbrake:
                        break
                    if not threads.appendNfire(extractJob,
                                        (self.app.staging.package,
                                         fid, saveto, self.app.staging.target)):
                        break
                    thread.progressCallback(self.app.staging.package.getFileById(fid))
                threads.stop()
                self.after_run(thread, "done %s %d files" % (self.opname[1], self.doneunits))
            self.worker.target = capsule
            fids = self.app.staging.package.searchFile(internalname, exact_match=False)
            self.numunits = len(fids)
            self.working = True
            self.doneunits = 0
            self.worker.start()
            return True
        return False

    def writepackage(self, destination):
        if self.can_start():
            self.opname = ["write modified", "written"]
            val = {"aborted": False}
            class dummyABRTiface:
                def __init__(self, val):
                    self.val = val
                def abort(self):
                    self.val["aborted"] = True
            def chkabrt():
                return val["aborted"]
            def capsule(thread):
                thread.abort_interface = dummyABRTiface(val)
                self.app.staging.writeout(destination, progresscback=thread.progressCallback, abort=chkabrt)
                if not thread.handbrake:
                    self.unsaved = False
                self.app.staging.target = destination
                self.after_run(thread, "done %s %d files" % (self.opname[1], self.doneunits))
            self.worker.target = capsule
            self.numunits = len(self.app.staging.package.files)
            self.working = True
            self.doneunits = 0
            self.worker.start()
            return True
        return False

    def stageAdd(self, fullname, mergemode=False):
        if os.path.isdir(fullname):
            self.app.staging.addDirectory(fullname, wholedir=not mergemode)
            self.unsaved = True
        else:
            addname, ok = self.app.inputbox("Import the file as", fullname)
            if ok:
                self.app.staging.addfile(addname, fullname)
                self.unsaved = True
        self.app.updateStagingScreen()

    def stageDel(self, internalname):
        fids = self.app.staging.package.searchFile(internalname, exact_match=False)
        if len(fids) > 0:
            self.unsaved = True
        for fid in fids:
            self.app.staging.remove_file(self.app.staging.package.getFileById(fid).name)
        self.app.updateStagingScreen()

    def stageUndo(self, internalname):
        self.unsaved = True
        self.app.staging.undoFile(internalname)
        self.app.updateStagingScreen()

    def stageUndoAll(self):
        self.unsaved = True
        names = list(map(attrgetter("name"), self.app.staging.appends)) +\
                list(map(attrgetter("name"), self.app.staging.deletes))
        for name in names:
            self.app.staging.undoFile(name.split(" ")[0])
        self.app.updateStagingScreen()

    def stageCommit(self):
        self.unsaved = True
        self.app.staging.commit()
        self.app.updatePACScreen()
        self.app.updateStagingScreen()