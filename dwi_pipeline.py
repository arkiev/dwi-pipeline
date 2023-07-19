import os
import pydra  
from pydra import Workflow, mark
from pydra.tasks.mrtrix3.latest import mrconvert, mrstats
from fileformats.medimage import NiftiGzXBvec, NiftiGzX

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGzXBvec, "t1w": NiftiGzX}
output_spec = {"dwi_preproc": NiftiGzXBvec}

# Create a workflow and add the dg task
wf = Workflow(name='my_workflow', input_spec=input_spec) 
wf.add(
    mrconvert(
        input=wf.lzin.dwi,
        coord=(3, 0),
        name="select_b0"
    )
)
wf.add(
    mrstats(
        input=wf.select_b0.lzout.output,
        name="mrstats"
    )
)

wf.set_output(("dwi_preproc", wf.mrstats.lzout.out_file))

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-01_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-01_t1w.nii.gz"
)
