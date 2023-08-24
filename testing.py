import os
import typing as ty
import pydra  
from pydra import Workflow, mark
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.latest import mrconvert, dwi2mask_fslbet, dwidenoise, mrdegibbs, dwifslpreproc, dwibiascorrect_fsl, mrgrid

from fileformats.medimage import NiftiGzXBvec, NiftiGz, MrtrixImage

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGz, "t1w": NiftiGz, "bvec": File, "bval": File}
output_spec = {"dwi_preproc": MrtrixImage}

# Create a workflow 
wf = Workflow(name='DWIpreproc_workflow', input_spec=input_spec) 

# code to import bval and bvec
@mark.task
def merge_grads(bvec: File, bval: File) -> ty.Tuple[File, File]:
    return (bvec, bval)

wf.add(
    merge_grads(
        bvec=wf.lzin.bvec,
        bval=wf.lzin.bval,
        name="merge_grads",
    )
)

# mrconvert (to combine bval and bvec with nifti)
wf.add(
    mrconvert.mrconvert(
        input=wf.lzin.dwi,
        fslgrad=wf.merge_grads.lzout.out,
        output="converted.mif",
        name="dwi_mif"
    )
)

# # dwi mask node
wf.add(
    dwi2mask_fslbet.dwi2mask_fslbet(
        input=wf.dwi_mif.lzout.output, 
        output="dwi_mask.mif",
        name="mask_node"
    )
)

# # regrid to 1mm iso - error mesage, (as issue?) revisit. 
wf.add(
    mrgrid.mrgrid(
        input=wf.mask_node.lzout.output.cast(MrtrixImage),
        operation="regrid",
        output="regridded.mif",
        name="regrid_node",
        voxel=[1.25] 
    )
)

wf.set_output(("dwi_preproc", wf.regrid_node.lzout.output))
# wf.set_output(("dwi_preproc", wf.denoise_node.lzout.out))
wf.cache_dir = output_path 

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-retest_T1w.nii.gz",
    bvec="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bvec",
    bval="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bval",
    plugin="serial",
)

print(f"Processed output generated at '{result.output.dwi_preproc}'")

# create_dotfile