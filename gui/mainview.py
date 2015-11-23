from PyQt4 import QtGui, QtCore
import os, sys

from gui import elements, adapter, controllR
from ovsylib import datastruct, fileadding_utils

class MainWindow(QtGui.QMainWindow):
    def __init__(self, title="MasterBlade Neptune"):
        QtGui.QMainWindow.__init__(self)
        self.operations = controllR.GeoFront(self)
        self.mainwidget = QtGui.QWidget(self)
        self.staging = None

        self.resize(1024, 500)
        self.setWindowTitle(title)
        self.setupLayout()
        self.setCentralWidget(self.mainwidget)
        self.showMaximized()

    def setupLayout(self):
        self.lvl1_vert = QtGui.QVBoxLayout()
        self.mainwidget.setLayout(self.lvl1_vert)
        elements.setToolbar(self)
        self.lvl2_horiz = QtGui.QHBoxLayout()
        self.lvl1_vert.addLayout(self.lvl2_horiz)
        elements.setVirtualDirView(self, self.lvl2_horiz)
        self.lvl3_vert = QtGui.QVBoxLayout()
        self.lvl2_horiz.addLayout(self.lvl3_vert)
        elements.setRealDirView(self, self.lvl3_vert)
        elements.setStagingView(self,self.lvl3_vert)
        self.lvl3_vert.setStretch(0, 1)
        self.lvl3_vert.setStretch(1, 0.5)
        self.lvl2_2_horiz = QtGui.QHBoxLayout()
        self.lvl1_vert.addLayout(self.lvl2_2_horiz)
        elements.bottombar(self, self.lvl2_2_horiz)

    def loadPAC(self):
        searchdir = QtCore.QDir.currentPath()
        """alterdir = os.path.join(adapter.getHome(), ".local", "share", "Steam", "SteamApps", "common")
        if os.path.isdir(alterdir):
            searchdir = alterdir"""
        fName = QtGui.QFileDialog.getOpenFileName(self,
                                                  "Load PAC file",
                                                  searchdir,
                                                  self.tr("All Files (*);;PAC Files (*.pac)"))
        if fName != "":
            self.staging = fileadding_utils.staging()
            try:
                self.statusText.setText("Loading %s" % self.staging.target)
                self.staging.loadPackage(fName)
            except FileNotFoundError as e:
                self.errorbox(str(e))
            self.updatePACScreen()
            self.statusText.setText("Ready")

    def newPAC(self):
        self.staging = fileadding_utils.staging()
        self.updateStagingScreen()
        self.statusText.setText("Ready")

    def updatePACScreen(self):
        def addItems(parent, elements):
            for text, children in elements:
                item = QtGui.QStandardItem(text)
                parent.appendRow(item)
                if children:
                    addItems(item, children)
        model = QtGui.QStandardItemModel()
        datastuff = adapter.listToTree(self.staging.package.listFileNames())
        model.setHorizontalHeaderLabels([self.staging.target])
        addItems(model, datastuff)
        self.virtdir.setModel(model)
        self.virtdir.setColumnWidth(0, elements.namecolumn_width)

    def updateStagingScreen(self):
        model = QtGui.QStandardItemModel()
        for datum in self.staging.listStagedCreate():
            item = QtGui.QStandardItem(datum)
            item.setIcon(QtGui.QIcon.fromTheme("list-add"))
            model.appendRow(item)
        for datum in self.staging.listStagedModify():
            item = QtGui.QStandardItem(datum)
            item.setIcon(QtGui.QIcon.fromTheme("view-refresh"))
            model.appendRow(item)
        for datum in self.staging.listStagedDelete():
            item = QtGui.QStandardItem(datum)
            item.setIcon(QtGui.QIcon.fromTheme("list-remove"))
            model.appendRow(item)

        self.stagingview.setModel(model)

    def getCurrentPackagePath(self, separator="\\"):
        indexes = self.virtdir.selectedIndexes()
        fullpath = []
        if len(indexes) > 0:
            index = indexes[0]
            while index.parent().isValid():
                fullpath.append(str(self.virtdir.model().data(index)))
                index = index.parent()
            fullpath.append(str(self.virtdir.model().data(index)))
        fullpath.reverse()
        if len(fullpath) > 0:
            return datastruct.adjustSeparatorForFS(separator.join(fullpath))
        return None

    def getCurrentComputerDirectory(self):
        alpha = self.getCurrentComputerPath()
        if alpha is None:
            return None
        if not os.path.isdir(alpha):
            return os.path.dirname(alpha)
        return alpha

    def getCurrentComputerPath(self):
        indexes = self.realdir.selectedIndexes()
        fullpath = []
        if len(indexes) > 0:
            index = indexes[0]
            while index.parent().isValid():
                fullpath.append(str(self.realdir.model().data(index)))
                index = index.parent()
            fullpath.append(str(self.realdir.model().data(index)))
        fullpath.reverse()
        if len(fullpath) > 0:
            return os.path.join(fullpath[0], *fullpath[1:])
        return None

    def test(self):
        print(self.getCurrentComputerPath())

    def abort(self):
        self.operations.abort()

    def updateProgress(self, num, text):
        self.progressBar.setValue(num)
        self.statusText.setText(text)

    def doneCback(self, text, maxoutbar=True):
        if maxoutbar:
            self.progressBar.setValue(100)
        self.statusText.setText(text)

    def itemmenu(self, position):
        saveto = self.getCurrentComputerDirectory()
        path = self.getCurrentPackagePath()
        menu = QtGui.QMenu()
        action_extract = menu.addAction(self.tr("Extract file/s"))
        action_stagedel = menu.addAction(self.tr("Stage file/s for deletion"))
        action = menu.exec_(self.virtdir.viewport().mapToGlobal(position))
        if action == action_extract:
            if saveto is None:
                self.errorbox("Please select an extraction directory")
            elif not self.operations.extract(path, saveto):
                self.errorbox("Please wait for the current operation to end")
        elif action == action_stagedel:
            self.operations.stageDel(path)

    def filemenu(self, position):
        path = self.getCurrentComputerPath()
        menu = QtGui.QMenu()
        action_import = menu.addAction(self.tr("Import file/s"))
        action = menu.exec_(self.realdir.viewport().mapToGlobal(position))
        if action == action_import:
            if self.staging is not None:
                self.operations.stageAdd(path)
            else:
                self.errorbox("Please load or create a .pac archive first")

    def extractAll(self):
        saveto = self.getCurrentComputerDirectory()
        if saveto is None:
            self.errorbox("Please select an extraction directory")
        elif not self.operations.extract("", saveto):
            self.errorbox("Please wait for the current operation to end")

    def errorbox(self, message):
        QtGui.QMessageBox.information(self, "Error!", message)

    def inputbox(self, message, default):
        return QtGui.QInputDialog.getText(self, "Confirm input" + " " * 150, message, text=default)

def launch():
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())