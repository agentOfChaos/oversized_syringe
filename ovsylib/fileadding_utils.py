from ovsylib import datastruct


class staging:

    def __init__(self, package):
        self.package = package
        self.replaces = {}
        self.appends = []

    def addfile(self, internal_name, path):
        collisions = self.package.searchFile(internal_name)
        if len(collisions) == 0:
            pass # stage append file
        elif len(collisions) == 1:
            pass # stage delete old, append new
        else:
            pass # error

    def addDirectory(self, dirpath):
        # list content
        # calculate relative names
        # add single files
        pass

    def commit(self):
        # apply staged commits
        # sort files by name
        pass