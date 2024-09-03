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
wf = Workflow(name='my_workflow', input_spec=input_spec, cache_dir=output_path) 

# # ##########################
# # # DWI brainmask example  #
# # ##########################

# create a brainmask
wf.add(
    dwi2mask.dwi2mask(
        input=wf.lzin.dwi,
        name="dwi2mask_rawDWI",
        algorithm="fslbet"
    )
)

wf.set_output(("dwi_brainmask", wf.dwi2mask_rawDWI.lzout.output)
)

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-01_t1w.nii.gz"
)