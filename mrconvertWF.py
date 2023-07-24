import os
import pydra  
from pydra import Workflow, mark
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.latest import mrconvert

from fileformats.medimage import NiftiGzXBvec, NiftiGzX

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGzXBvec, "t1w": NiftiGzX, "bvec": File, "bval": File}
output_spec = {"dwi_preproc": NiftiGzXBvec}

# Create a workflow and add the dg task
wf = Workflow(name='my_workflow', input_spec=input_spec) 

#mrconvert
wf.add(
    mrconvert.mrconvert(
        input=wf.lzin.dwi,
        fslgrad=[wf.lzin.bvec, wf.lzin.bval],
        name="dwi_mif"
    )
)


# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-01_t1w.nii.gz",
    bvec="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bvec",
    bval="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bval"
)