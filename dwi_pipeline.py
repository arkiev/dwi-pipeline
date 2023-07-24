import os
import pydra  
from pydra import Workflow, mark
from pydra.tasks.mrtrix3.latest import mrconvert, mrstats
from pydra.tasks.mrtrix3.latest import dwi2mask, dwidenoise, mrdegibbs, dwifslpreproc, dwibiascorrect

from fileformats.medimage import NiftiGzXBvec, NiftiGzX

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGzXBvec, "t1w": NiftiGzX}
output_spec = {"dwi_preproc": NiftiGzXBvec}

# Create a workflow and add the dg task
wf = Workflow(name='my_workflow', input_spec=input_spec) 

#################
# EXAMPLE USAGE #
#################
# wf.add(
#     mrconvert(
#         input=wf.lzin.dwi,
#         coord=(3, 0),
#         name="select_b0"
#     )
# )

# mrstats node included as another example 
# wf.add(
#     mrstats(
#         input=wf.select_b0.lzout.output,
#         name="mrstats"
#     )
# )

# # ######################
# # # DWI preprocessing  #
# # ######################

# create a brainmask
wf.add(
    dwi2mask.dwi2mask(
        input=wf.lzin.dwi,
        name="dwi2mask_rawDWI",
        algorithm="fslbet"
   )
)

# dwidenoise node
wf.add(
    dwidenoise(
        input=wf.lzin.dwi,
        name="dwidenoise",
        mask=wf.dwi2mask_rawDWI.lzout.output,
    )
)

# degibbs node
wf.add(
    mrdegibbs(
        input=wf.dwidenoise.lzout.output,
        name="degibbs"
    )
)

# DWI did not come with se_epi or blip image. Let's use rpe_none (as opposed to SynB0)

# dwifslpreproc node
wf.add(
    dwifslpreproc(
        input=wf.degibbs.lzout.output,
        name="dwifslpreproc",
        rpe_none=True,
        eddy_options=" --slm=linear"
    )
)

# create a brainmask
wf.add(
    dwi2mask(
        input=wf.dwifslpreproc.lzout.output,
        name="dwi2mask_correctedDWI",
        algorithm="fslbet"
    )
)

# dwibiascorrect node
wf.add(
    dwibiascorrect(
        input=wf.dwifslpreproc.lzout.output,
        algorithm="ants",
        name="dwibiascorrect",
        mask=wf.dwi2mask_correctedDWI.lzout.output,
    )
)

# reslice DWI
wf.add(
    mrgrid(
        input=wf.dwibiascorrect.lzout.output,
        name="mrgrid_dwi",
        operation="regrid",
        voxel=1,
    )
)

# reslice brainmask
wf.add(
    mrgrid(
        input=wf.dwi2mask_correctedDWI.lzout.output,
        name="dwi2mask_correctedDWI_regridded",
        operation="regrid_brainmask",
        template=wf.dwibiascorrect.lzout.output,
    )
)

wf.set_output(("dwi_preproc", wf.mrgrid_dwi.lzout.output), 
    ("dwi_brainmask", wf.regrid_brainmask.lzout.output)
)

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-01_t1w.nii.gz"
)
