import os
import nipype
import pydra  

from nipype import DataGrabber, Node, SelectFiles, DataSink
import nipype.pipeline.engine as pe

# Define the directory where the images are located
data_dir = '/Users/arkievdsouza/Documents/NIFdata/ds000114'

# Define the wildcard pattern to match the image files
file_pattern = "*.nii.gz"

# Create a DataGrabber node to find the images
dg = Node(DataGrabber(infields=['subject_id'], outfields=['image_files']),
          name='datagrabber')
dg.inputs.base_directory = data_dir
dg.inputs.template = '*'  # search all subdirectories
dg.inputs.sort_filelist = True
dg.inputs.field_template = dict(image_files=file_pattern)
dg.inputs.subject_id = '*'  # match all subjects

# Define a simple workflow with just the DataGrabber node
wf = pe.Workflow(name='image_grabber_wf', base_dir='./output')
wf.add_nodes([dg])

# Run the workflow
wf.run()
