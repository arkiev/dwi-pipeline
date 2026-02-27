from pathlib import Path
import typing as ty
from fileformats.core import FileSet, extra_implementation, validated_property
from fileformats.generic import BinaryFile
from fileformats.application.archive import BaseGzip
from fileformats.core.mixin import WithMagicNumber
from fileformats.core.exceptions import FormatMismatchError
import fileformats.medimage


class MultiLineMetadataValue(list):
    pass


class BaseMrtrixImage(WithMagicNumber, fileformats.medimage.MedicalImage, BinaryFile):

    magic_number = b"mrtrix image\n"
    binary = True

    @validated_property
    def data_fspath(self):
        data_fspath = self.metadata["file"].split()[0]
        if data_fspath == ".":
            data_fspath = self.fspath
        elif Path(data_fspath).parent == Path("."):
            data_fspath = self.fspath.parent / data_fspath
        else:
            data_fspath = Path(data_fspath).relative_to(self.fspath.parent)
        return data_fspath

    @property
    def data_offset(self):
        fspath_and_offset = self.metadata["file"].split()
        assert len(fspath_and_offset) <= 2
        return int(fspath_and_offset[1]) if len(fspath_and_offset) > 1 else 0

    @property
    def vox_sizes(self):
        return self.metadata["vox"]

    @property
    def dims(self):
        return self.metadata["dim"]


class ImageFormat(BaseMrtrixImage):

    ext = ".mif"
    iana_mime = "application/x-mrtrix-image-format"

    @validated_property
    def _check_data_file(self):
        if self.data_fspath != self.fspath:
            raise FormatMismatchError(
                f"Data file ('{self.data_fspath}') is not set to the same file as header "
                f"('{self.fspath}')"
            )

    @property
    def data_file(self):
        return self


class ImageFormatGz(fileformats.medimage.MedicalImage, BaseGzip):

    archived_type = ImageFormat
    iana_mime = "application/x-mrtrix-image-format-gz"
    ext = ".mif.gz"


class ImageHeader(BaseMrtrixImage):

    ext = ".mih"
    iana_mime = "application/x-mrtrix-image-header"

    @validated_property
    def data_file(self):
        return ImageDataFile(self.data_fspath)

    def __attrs_post_init__(self):
        if len(self.fspaths) == 1:
            # add in data file if only header file is provided
            self.fspaths |= set([BaseMrtrixImage(self.fspath).data_fspath])
        super().__attrs_post_init__()


class ImageDataFile(BinaryFile):

    ext = ".dat"


@extra_implementation(FileSet.read_metadata)
def mrtrix_read_metadata(
    mif: BaseMrtrixImage, **kwargs: ty.Any
) -> ty.Mapping[str, ty.Any]:
    metadata = {}
    with open(mif.fspath, "rb") as f:
        line = f.readline()
        if line != mif.magic_number:
            raise FormatMismatchError(
                f"Magic line {line} doesn't match reference {mif.magic_number}"
            )
        line = f.readline().decode("utf-8")
        while line and line != "END\n":
            key, value = line.split(": ", maxsplit=1)
            if "," in value:
                try:
                    value = [int(v) for v in value.split(",")]
                except ValueError:
                    try:
                        value = [float(v) for v in value.split(",")]
                    except ValueError:
                        pass
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            if key in metadata:
                if isinstance(metadata[key], MultiLineMetadataValue):
                    metadata[key].append(value)
                else:
                    metadata[key] = MultiLineMetadataValue([metadata[key], value])
            else:
                metadata[key] = value
            line = f.readline().decode("utf-8")
    return metadata
