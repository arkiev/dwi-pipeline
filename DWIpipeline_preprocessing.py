import typing as ty
import attrs
import os
from pathlib import Path
from ast import alias

import pydra
from pydra import Workflow, mark, ShellCommandTask
from pydra.engine.task import FunctionTask
from pydra.engine.specs import (
    SpecInfo,
    BaseSpec,
    ShellSpec,
    ShellOutSpec,
    File,
)
from pydra.tasks.mrtrix3 import (
    DwiDenoise,
    MrDegibbs,
    DwiFslpreproc,
    DwiBiasnormmask,
    Dwi2Mask_Fslbet,
    DwiBiascorrect_Ants,
    DwiBiascorrect_Fsl,
    MrGrid,
    Dwi2Response_Dhollander,
)
from pydra.tasks.fastsurfer.latest import Fastsurfer
from pydra.tasks.fsl.auto import EpiReg

from fileformats.generic import Directory, DirectoryOf
from fileformats.medimage import NiftiGz, NiftiGzXBvec

# REMOVED: problematic mrtrix3 fileformats import
# from fileformats.medimage_mrtrix3 import (
#     ImageFormat as Mif,
#     ImageFormat,
#     ImageIn,
#     ImageOut,
#     Tracks,  # noqa: F401
# )

# Define the path and output_path variables
output_path = "/Users/adso8337/Desktop/DWIpipeline_testing/Outputs/"


@pydra.mark.task
def run_mri_synthstrip():
    import subprocess

    # Define the command to execute
    command = ["python", "/Users/arkievdsouza/synthstrip-docker"]
    # Execute the command
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Check if the command executed successfully
    if result.returncode != 0:
        # Print error message if the command failed
        print("Error running mri_synthstrip:")
        print(result.stderr.decode())
    # Return the stdout output
    return result.stdout.decode()


# Define the input_spec for the workflow
input_spec = {
    "dwi_preproc_mif": File,
    # "FS_dir": str,
    # "fTTvis_image_T1space": File,
    # "fTT_image_T1space": File,
    # "parcellation_image_T1space": File,
}

# Create a workflow
wf = Workflow(
    name="DWIpipeline_wf",
    input_spec=input_spec,
    cache_dir=output_path,
)  # output_spec=output_spec)

# denoise
wf.add(
    DwiDenoise(
        name="dwi_denoise_task",
        dwi=wf.lzin.dwi_preproc_mif,
    )
)

# unring
wf.add(
    MrDegibbs(
        name="dwi_degibbs_task",
        in_file=wf.dwi_denoise_task.lzout.out,
    )
)

# motion and distortion correction (eddy, topup) - placeholder

# create brainmask and mask DWI image - revisit
# wf.add(
#     DwiBiasnormmask(
#         name="dwibiasnormmask_task",
#         in_file=wf.dwi_degibbs_task.lzout.out, # update to be output of DWIfslpreproc
#         output_dwi="dwi_biasnorm.mif",
#         output_mask="dwi_mask.mif",
#         mask_algo="threshold",
#         output_bias="bias_field.mif",
#         output_tissuesum="tissue_sum.mif"
#     )
# )

wf.add(
    Dwi2Mask_Fslbet(
        name="dwimask_task",
        in_file=wf.dwi_degibbs_task.lzout.out,  # update to be output of DWIfslpreproc
        out_file="dwi_mask.mif.gz",
    )
)

wf.add(
    DwiBiascorrect_Fsl(  # replace this with ANTs
        name="dwibiasfieldcorr_task",
        in_file=wf.dwi_degibbs_task.lzout.out,
        mask=wf.dwimask_task.lzout.out_file,
        bias="biasfield.mif.gz",
    )
)

# # Step 7: Crop images to reduce storage space (but leave some padding on the sides)

# #CONSIDER ADDING 'REGRID' HERE!

# grid DWI
wf.add(
    MrGrid(
        in_file=wf.dwibiasfieldcorr_task.lzout.out_file,
        name="crop_task_dwi",
        operation="crop",
        mask=wf.dwimask_task.lzout.out_file,
        out_file="dwi_processed.mif.gz",
        uniform=-3,
    )
)

# grid dwimask
wf.add(
    MrGrid(
        in_file=wf.dwimask_task.lzout.out_file,
        name="crop_task_mask",
        operation="crop",
        mask=wf.dwimask_task.lzout.out_file,
        out_file="dwimask_procesesd.mif.gz",
        interp="nearest",
        uniform=-3,
    )
)

# # Estimate Response Function (subject)
wf.add(
    Dwi2Response_Dhollander(
        name="EstimateResponseFcn_task",
        in_file=wf.crop_task_dwi.lzout.out_file,
        mask=wf.crop_task_mask.lzout.out_file,
        voxels="voxels.mif.gz",
    )
)

# # SET WF OUTPUT
wf.set_output(("DWI_processed", wf.crop_task_dwi.lzout.out_file))
wf.set_output(("DWImask_processed", wf.crop_task_mask.lzout.out_file))

# ########################
# # Execute the workflow #
# ########################

result = wf(
    dwi_preproc_mif="/Users/adso8337/Desktop/DWIpipeline_testing/Data/test001/DWI.mif.gz",
    plugin="serial",
)
