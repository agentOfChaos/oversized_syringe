import struct


from ovsylib import datamover, compression, customsort
from ovsylib.utils.binary import put_string, get_string
from ovsylib.utils.filenames import adjustSeparatorForFS, adjustSeparatorForPac
from ovsylib.utils.constants import intsize
from ovsylib.utils.container import HydraContainer



class PacFile(GenericDataStruct):

    def __init__(self, parent_data_struct=None):
        super().__init__(parent_data_struct)
        self.file_counter = HydraContainer(0)
        self.header = None
        self.directory = []

    def build_from_file(self, binfile):
        self.header = PacFileHeader(self.file_counter, parent_data_struct=self).build_from_file(binfile)
        return super().build_from_file(binfile)

    def build_empty(self):
        self.header = PacFileHeader(self.file_counter, parent_data_struct=self).build_empty()
        return super().build_empty()

    def get_child_displacement(self, child):
        if child == self.header:
            return 0
        # stuff
        else:
            return 0
