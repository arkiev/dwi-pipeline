import os
import pydra  
from pydra import Workflow, mark
from pydra.tasks.mrtrix3.latest import mrconvert, mrstats
from pydra.tasks.mrtrix3.latest import fivetissuetype2vis
from fileformats.medimage import NiftiGzXBvec, NiftiGzX

# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"fTT": NiftiGzX}
output_spec = {"vis_image": "output vis image"}

# Create a workflow and add the dg task
wf = Workflow(name='anat_workflow', input_spec=input_spec, cache_dir=output_path) 

# # #####################
# # # create 5TTvis image  #
# # #####################

wf.add(
    fivetissuetype2vis(
        input=wf.lzin.fTT,
        name="fTT2vis"
    )
)

wf.set_output(("anat_workflow", wf.fTT2vis.lzout.output)
)

# Execute the workflow
result = wf(
    fTT_image="/Users/arkievdsouza/git/dwi-pipeline/working-dir/100307_5TThsvs_Registered.mif.gz"
)