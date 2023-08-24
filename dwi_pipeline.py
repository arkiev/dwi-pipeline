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

# # dwi denoise node
wf.add(
    dwidenoise.dwidenoise(
        name="denoise_node",
        dwi=wf.dwi_mif.lzout.output, 
        out="denoised.mif", 
        rank="rank.mif",
        noise="noise.mif",
        mask=wf.mask_node.lzout.output.cast(MrtrixImage)  
    )
)

# # # dwi unring node
wf.add(
    mrdegibbs.mrdegibbs(
        name="gibbscorr_node",
        out="gibbs_corrected.mif",
        input=wf.denoise_node.lzout.out
        #**{'in': wf.dwi_mif.lzout.output}
    )
)

# motion and distortion correction node
wf.add(
    dwifslpreproc.dwifslpreproc(
        name="motdistcorr_node",
        input=wf.gibbscorr_node.lzout.out,
        output="motdist_corrected.mif",
        rpe_none=True,
        pe_dir="PA",  # change to header 
        eddy_mask=wf.mask_node.lzout.output.cast(MrtrixImage)   
    )
)

# Bias field correction (skip since algorithm needs to be specified)
wf.add(
    dwibiascorrect_fsl.dwibiascorrect_fsl(
        name="biascorrect_node",
        input=wf.motdistcorr_node.lzout.output,
        output="bias_corrected.mif",
        mask=wf.mask_node.lzout.output    
        )
)

# # regrid processed DWI to 1.25mm iso
wf.add(
    mrgrid.mrgrid(
        input=wf.biascorrect_node.lzout.output.cast(MrtrixImage),
        operation="regrid",
        output="PreprocessedDWI.mif",
        name="regrid_node",
        voxel=[1.25] 
    )
)


# # regrid DWI brainmask to 1.25mm iso
wf.add(
    mrgrid.mrgrid(
        input=wf.mask_node.lzout.output.cast(MrtrixImage),
        operation="regrid",
        output="DWIbrainmask_regridded.mif",
        name="regridmask_node",
        interpolation="nearest",
        voxel=[1.25,1,2] 
    )
)

wf.set_output(("dwi_preproc", wf.regrid_node.lzout.output))
wf.set_output(("dwi_preproc_mask", wf.regridmask_node.lzout.output))

# wf.set_output(("dwi_preproc", wf.regrid_node.lzout.output),
#               ("dwibrainmask_preproc", wf.regridmask_node.lzout.output)
#               )

# wf.set_output(("dwi_preproc", wf.biascorrect_node.lzout.output))
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