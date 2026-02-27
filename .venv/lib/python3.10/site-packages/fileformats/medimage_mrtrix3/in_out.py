import sys
import typing as ty
from fileformats.medimage import (
    DicomImage,
    DicomDir,
    NiftiGzX,
    NiftiGz,
    NiftiX,
    Nifti1,
    Nifti2,
    Mgh,
    MghGz,
    Analyze,
    NiftiBvec,
    NiftiGzBvec,
    NiftiXBvec,
    NiftiGzXBvec,
)
from .image import ImageFormat, ImageHeader, ImageFormatGz
from .dwi import (
    NiftiB,
    NiftiGzB,
    NiftiGzXB,
    NiftiXB,
    ImageFormatB,
    ImageFormatGzB,
    ImageHeaderB,
)

if sys.version_info >= (3, 9):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


ImageIn: TypeAlias = ty.Union[
    DicomImage,
    DicomDir,
    ImageFormat,
    ImageFormatGz,
    ImageHeader,
    ImageFormatB,
    ImageFormatGzB,
    ImageHeaderB,
    NiftiGzX,
    NiftiGz,
    NiftiX,
    Nifti1,
    Nifti2,
    NiftiB,
    NiftiGzB,
    NiftiGzXB,
    NiftiXB,
    NiftiBvec,
    NiftiGzBvec,
    NiftiXBvec,
    NiftiGzXBvec,
    Mgh,
    MghGz,
    Analyze,
]

ImageOut: TypeAlias = ty.Union[
    ImageFormat,
    ImageFormatGz,
    ImageHeader,
    ImageFormatB,
    ImageFormatGzB,
    ImageHeaderB,
    NiftiGzX,
    NiftiGz,
    NiftiX,
    Nifti1,
    Nifti2,
    NiftiB,
    NiftiGzB,
    NiftiGzXB,
    NiftiXB,
    NiftiBvec,
    NiftiGzBvec,
    NiftiXBvec,
    NiftiGzXBvec,
    Mgh,
    MghGz,
    Analyze,
]
