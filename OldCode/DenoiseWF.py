import os
import typing as ty
import pydra  
from pydra import Workflow
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.v3_0 import mrconvert, dwidenoise
from fileformats.medimage import NiftiGzXBvec, NiftiGz
from fileformats.medimage_mrtrix3 import ImageFormat

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGz, "t1w": NiftiGz, "bvec": File, "bval": File}
output_spec = {"dwi_preproc": File}


@pydra.mark.task
def merge_grads(bvec: File, bval: File) -> ty.List[File]:
    return [bvec, bval]


# Create a workflow and add the mrconvert task
wf = Workflow(name='dwi_denoise_wf', input_spec=input_spec, cache_dir=output_path) 

wf.add(
    merge_grads(
        bvec=wf.lzin.bvec,
        bval=wf.lzin.bval,
        name="merge_grads",
    )
)

# Convert to mif 
wf.add(
    mrconvert(
        input=wf.lzin.dwi,
        output="dwi.mif",
        name="convert_DWI",
        fslgrad=wf.merge_grads.lzout.out,
    )
)

# Apply dwidenoise
wf.add(
    dwidenoise(
        name="denoise_node",
        dwi=wf.convert_DWI.lzout.output, 
        out="denoised.mif", 
        rank="rank.mif",
        noise="noise.mif" #, mask=wf.mask_node.lzout.output.cast(MrtrixImage)  
    )
)

wf.set_output(("denoised", wf.denoise_node.lzout.out))

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-retest_T1w.nii.gz",
    bvec="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bvec",
    bval="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bval",
    plugin="serial",
)
