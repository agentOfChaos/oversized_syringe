from PyQt4 import QtGui, QtCore

from gui import treeview

"""
Here goes the "dumb" part of the gui, the one that only describe the layout / look and,
only in minimal part, the behaviout
"""

namecolumn_width = 300

def setToolbar(object):

    createf = QtGui.QAction(QtGui.QIcon.fromTheme("document-new"), "New", object)
    createf.setShortcut("Ctrl+N")
    createf.setStatusTip("Create a new .pac archive")
    object.connect(createf, QtCore.SIGNAL('triggered()'), object.newPAC)

    openf = QtGui.QAction(QtGui.QIcon.fromTheme("folder-open"), "Open", object)
    openf.setShortcut("Ctrl+O")
    openf.setStatusTip("Open a *.pac file")
    object.connect(openf, QtCore.SIGNAL('triggered()'), object.loadPAC)

    info = QtGui.QAction(QtGui.QIcon.fromTheme("dialog-information"), "Info", object)
    info.setShortcut("Ctrl+I")
    info.setStatusTip("Show information")
    object.connect(info, QtCore.SIGNAL('triggered()'), object.showInfo)

    abrt = QtGui.QAction(QtGui.QIcon.fromTheme("process-stop"), "Abort", object)
    abrt.setStatusTip("Abort any running operation")
    object.connect(abrt, QtCore.SIGNAL('triggered()'), object.abort)

    xtractall = QtGui.QAction(QtGui.QIcon.fromTheme("mail-forward"), "Extract all", object)
    xtractall.setShortcut("Ctrl+X")
    xtractall.setStatusTip("Extract the pac directory")
    object.connect(xtractall, QtCore.SIGNAL('triggered()'), object.extractAll)

    commitcall = QtGui.QAction(QtGui.QIcon.fromTheme("weather-clear"), "Commit", object)
    commitcall.setStatusTip("Commit staged changes")
    object.connect(commitcall, QtCore.SIGNAL('triggered()'), object.commitChanges)

    writecall = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), "Write", object)
    writecall.setStatusTip("Write modifies to disk")
    object.connect(writecall, QtCore.SIGNAL('triggered()'), object.writeTo)

    object.top_toolbar = object.addToolBar('Main toolbar')
    object.top_toolbar.addAction(createf)
    object.top_toolbar.addAction(openf)
    object.top_toolbar.addAction(xtractall)
    object.top_toolbar.addAction(commitcall)
    object.top_toolbar.addAction(writecall)
    object.top_toolbar.addAction(abrt)
    object.top_toolbar.addAction(info)
    object.top_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

def setVirtualDirView(object, layout):
    object.virtdir = treeview.CoolTreeView()
    object.virtdir.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    object.virtdir.customContextMenuRequested.connect(object.itemmenu)
    layout.addWidget(object.virtdir)

def setRealDirView(object, layout):
    object.realdir = treeview.CoolTreeView()
    object.realdirmodel = QtGui.QFileSystemModel()
    object.realdirmodel.setRootPath( QtCore.QDir.currentPath() )
    object.realdir.setModel(object.realdirmodel)
    object.realdir.setColumnWidth(0, namecolumn_width)
    object.realdir.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    object.realdir.customContextMenuRequested.connect(object.filemenu)
    layout.addWidget(object.realdir)
    object.realdir.expand_path(QtCore.QDir.currentPath())

def setStagingView(object, layout):
    object.stagingview = QtGui.QListView()
    object.stagingviewmodel = QtGui.QStandardItemModel()
    object.stagingview.setModel(object.stagingviewmodel)
    object.stagingview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    object.stagingview.customContextMenuRequested.connect(object.stagemenu)
    layout.addWidget(object.stagingview)

def bottombar(object, layout):
    object.progressBar = QtGui.QProgressBar(object.mainwidget)
    object.progressBar.setRange(0, 100)
    object.progressBar.setValue(0)
    object.progressBar.setTextVisible(True)
    object.progressBar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
    layout.addWidget(object.progressBar)

    object.statusText = QtGui.QLabel('Please load or create a pac archive')
    object.statusText.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
    layout.addWidget(object.statusText)
