from ast import alias
import os
import typing as ty
import pydra
from pydra import Workflow, mark, ShellCommandTask
from pydra.engine.specs import File
from pydra.tasks.mrtrix3.v3_0 import (
    DwiDenoise,
    MrDegibbs,
    DwiFslpreproc,
    DwiBiasnormmask,
    Dwi2Mask_Fslbet,
    DwiBiascorrect_Ants,
    DwiBiascorrect_Fsl,
    TransformConvert,
    MrTransform,
    MrConvert,
    MrGrid,
    DwiExtract,
    MrCalc,
    MrMath,
    DwiBiasnormmask,
    MrThreshold,
    Dwi2Response_Dhollander,
    Dwi2Fod,
    MtNormalise,
    TckGen,
    TckSift2,
    Tck2Connectome,
    TckMap,
)
from pydra.tasks.fsl.auto import EpiReg
from pydra.engine.specs import SpecInfo, BaseSpec, ShellSpec, ShellOutSpec
from fileformats.medimage import NiftiGzXBvec, NiftiGz
from fileformats.medimage_mrtrix3 import ImageFormat
from pathlib import Path
from fileformats.medimage_mrtrix3 import ImageIn, ImageOut, Tracks  # noqa: F401

# Define the path and output_path variables
output_path = "/Users/arkievdsouza/git/dwi-pipeline/working-dir/"


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
    "FS_dir": str,
    "fTTvis_image_T1space": File,
    "fTT_image_T1space": File,
    "parcellation_image_T1space": File,
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
wf.set_output(("T1_registered", wf.transformT1_task.lzout.out_file))
wf.set_output(("fTT_registered", wf.transform5TT_task.lzout.out_file))
wf.set_output(("fTTvis_registered", wf.transform5TTvis_task.lzout.out_file))
# wf.set_output(("Parcellation_registered", wf.transformParcellation_task.lzout.out_file))
# wf.set_output(("DWI_processed", wf.crop_task_dwi.lzout.out_file))
# wf.set_output(("DWImask_processed", wf.crop_task_mask.lzout.out_file))
# wf.set_output(("sift_mu", wf.SIF2_task.lzout.out_mu))
# wf.set_output(("sift_weights", wf.SIF2_task.lzout.out_weights))
wf.set_output(("wm_fod_norm", wf.NormFod_task.lzout.fod_wm_norm))
# wf.set_output(("conenctome_file", wf.connectomics_task.lzout.connectome_out))
wf.set_output(("TDI_file", wf.TDImap_task.lzout.out_file))
wf.set_output(("DECTDI_file", wf.DECTDImap_task.lzout.out_file))
# wf.set_output(("tractogram", wf.tckgen_task.lzout.tracks))
# wf.set_output(("fTTreg", wf.transform5TT_task.lzout.out_file))
# wf.set_output(("fTTreg", wf.meanb0_task.lzout.out_file))
# wf.set_output(("tform", wf.transformconvert_task.lzout.out_file))

# wf.set_output(("epireg", wf.epi_reg_task.lzout.matrix))

# ########################
# # Execute the workflow #
# ########################

result = wf(
    dwi_preproc_mif="/Users/arkievdsouza/Desktop/ConnectomeBids/data/sub-01/dwi/sub-01_DWI.mif.gz",
    FS_dir="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/Fastsurfer_b5d77a6efac5b7efedbd561a717bdbc6/subjects_dir/FS_outputs/",
    fTTvis_image_T1space="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/5TTvis_hsvs.mif.gz",
    fTT_image_T1space="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/5TT_hsvs.mif.gz",
    parcellation_image_T1space="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/Atlas_desikan.mif.gz",
    plugin="serial",
)


# # Step 7: Crop images to reduce storage space (but leave some padding on the sides) - pointing to wrong folder, needs fix (nonurgent)
# # grid DWI
# wf.add(
#     mrgrid(
#         input=wf.dwibiasnormmask_task.lzout.output_dwi,
#         name="crop_task_dwi",
#         operation="crop",
#         output="dwi_crop.mif",
#         mask=wf.dwibiasnormmask_task.lzout.output_mask,
#         uniform=-3,
#     )
# )

# #grid dwimask
# wf.add(
#     mrgrid(
#         input=wf.dwibiasnormmask_task.lzout.output_mask,
#         name="crop_task_mask",
#         operation="crop",
#         output="mask_crop.mif",
#         mask=wf.dwibiasnormmask_task.lzout.output_mask,
#         uniform=-3,
#     )
# )
