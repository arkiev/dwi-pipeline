import os
from pydra import Workflow
import pydra 


# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/t1-pipeline/working-dir'

# Define the subject_list and session_list variables
subject_list = [1,2]
session_list = ['retest']

# Create a container task to run the DataGrabber
def datagrabber(subject_id, session_id):
    from nipype.interfaces.io import DataGrabber
    dg = DataGrabber(infields=['subject_id', 'session_id'], outfields=['anat', 'dwi'])
    dg.inputs.base_directory = path
    dg.inputs.template = '*'
    dg.inputs.sort_filelist = True
    dg.inputs.template_args = {'anat': [['subject_id', 'session_id']],
                               'dwi': [['subject_id', 'session_id']]}
    dg.inputs.field_template = {'anat': 'sub-%02d/ses-%s/anat/*_T1w.nii.gz',
                                'dwi': 'sub-%02d/ses-%s/dwi/*_dwi.nii.gz',
                                }
    dg.inputs.subject_id = subject_id
    dg.inputs.session_id = session_id
    result = dg.run()
    return result.outputs

# Create a container task to print the output path
def print_output_path(subject_id, session_id):
    print(f"Output Path for subject {subject_id}, session {session_id}: {output_path}")


# Define the input_spec for the workflow
input_spec = {"subject_id": int, "session_id": str}

# Create a workflow
wf = Workflow(name="nipype_workflow_datagrabber", input_spec=input_spec)

