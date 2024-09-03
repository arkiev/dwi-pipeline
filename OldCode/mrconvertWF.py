import os
import typing as ty
import pydra  
from pydra import Workflow
from pydra import mark
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.v3_0 import mrconvert
from fileformats.medimage import NiftiGzXBvec, NiftiGz
from fileformats.medimage_mrtrix3 import ImageFormat


# Define the path and output_path variables
path = '/Users/arkievdsouza/Documents/NIFdata/ds000114'
output_path = '/Users/arkievdsouza/git/dwi-pipeline/working-dir'

# Define the input_spec for the workflow
input_spec = {"dwi": NiftiGz, "t1w": NiftiGz, "bvec": File, "bval": File}
output_spec = {"dwi_preproc": ImageFormat}

# Create a workflow and add the dg task
wf = Workflow(name='my_workflow', input_spec=input_spec, cache_dir=output_path) 

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

# mrconvert
wf.add(
    mrconvert(
        input=wf.lzin.dwi,
        fslgrad=wf.merge_grads.lzout.out,
        output="converted.mif",
        # json_export="json_export.txt",
        # export_grad_mrtrix="grad_matrix_export.txt",
        # export_grad_fsl=["bvec", "bval"],
        # export_pe_table="export_pe_table.txt",
        # export_pe_eddy=["bvec_eddy", "bval_eddy"],
        name="dwi_mif"
    )
)

wf.set_output(("dwi_preproc", wf.dwi_mif.lzout.output))


# Execute the workflow
result = wf(
    dwi="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/dwi/sub-01_ses-retest_dwi.nii.gz",
    t1w="/Users/arkievdsouza/Documents/NIFdata/ds000114/sub-01/ses-retest/anat/sub-01_ses-retest_T1w.nii.gz",
    bvec="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bvec",
    bval="/Users/arkievdsouza/Documents/NIFdata/ds000114/dwi.bval",
    plugin="serial",
)

# print(f"Processed output generated at '{result.output.dwi_preproc}'")