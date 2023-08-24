import os
import pydra  
from pydra import Workflow
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.v3_0 import mrconvert, dwidenoise
from fileformats.medimage import NiftiGzXBvec, NiftiGzX

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGzX, "t1w": NiftiGzX, "bvec": File, "bval": File}
output_spec = {"dwi_preproc": File}

# Create a workflow and add the mrconvert task
wf = Workflow(name='dwi_denoise_wf', input_spec=input_spec, cache_dir=output_path) 

# Convert to mif 
wf.add(
    mrconvert.mrconvert(
        input=wf.lzin.dwi,
        name="convert_DWI",
        fslgrad=[wf.lzin.bvec, wf.lzin.bval]
    )
)

# Apply dwidenoise
wf.add(
    dwidenoise.dwidenoise(
        input=wf.convert_DWI.lzout.out,
        name="denoise_DWIfslgrad",
    )
)

# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-01_t1w.nii.gz",
    bvec="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bvec",
    bval="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bval"
)
