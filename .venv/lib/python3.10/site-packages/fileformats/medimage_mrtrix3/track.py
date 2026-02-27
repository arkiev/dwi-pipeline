from fileformats.generic import BinaryFile
from fileformats.core.mixin import WithMagicNumber


class Tracks(WithMagicNumber, BinaryFile):

    ext = ".tck"
    magic_number = b"mrtrix tracks\n"
    binary = True
