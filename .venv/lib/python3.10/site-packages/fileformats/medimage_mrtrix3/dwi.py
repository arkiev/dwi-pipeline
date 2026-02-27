from fileformats.core import validated_property
from fileformats.core.mixin import WithAdjacentFiles
from fileformats.medimage import DwiEncoding, Nifti1, NiftiGz, NiftiX, NiftiGzX
from .image import ImageFormat, ImageHeader, ImageFormatGz


class BFile(DwiEncoding):
    """MRtrix-style diffusion encoding, all in one file"""

    ext = ".b"


# NIfTI file format gzipped with BIDS side car
class WithBFile(WithAdjacentFiles):
    @validated_property
    def encoding(self) -> BFile:
        return BFile(self.select_by_ext(BFile))


class NiftiB(WithBFile, Nifti1):
    iana_mime = "application/x-nifti2+b"


class NiftiGzB(WithBFile, NiftiGz):
    iana_mime = "application/x-nifti2+gzip.b"


class NiftiXB(WithBFile, NiftiX):
    iana_mime = "application/x-nifti2+json.b"


class NiftiGzXB(WithBFile, NiftiGzX):
    iana_mime = "application/x-nifti2+gzip.json.b"


class ImageFormatB(WithBFile, ImageFormat):
    iana_mime = "application/x-mrtrix-image-format.b"


class ImageFormatGzB(WithBFile, ImageFormatGz):
    iana_mime = "application/x-mrtrix-image-format+gzip.b"


class ImageHeaderB(WithBFile, ImageHeader):
    iana_mime = "application/x-mrtrix-image-header.b"
