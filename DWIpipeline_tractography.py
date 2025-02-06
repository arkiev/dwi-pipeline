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
    "dwi_mask_mif": File,
    "FS_dir": str,
    "fTT_image_T1space": File,
    "parcellation_image_T1space": File,
    "avg_respfcn_WM": File,
    "avg_respfcn_GM": File,
    "avg_respfcn_CSF": File,
}

# Create a workflow
wf = Workflow(
    name="DWIpipeline_wf",
    input_spec=input_spec,
    cache_dir=output_path,
)  # output_spec=output_spec)

# # ########################
# # # REGISTRATION CONTENT #
# # ########################


# Step 8: Generate target images for DWI->T1 registration
@mark.task
@mark.annotate(
    {
        "FS_dir": str,
        "return": {
            "t1_FSpath": str,
            "t1brain_FSpath": str,
            "wmseg_FSpath": str,
            "normimg_FSpath": str,
        },
    }
)
def join_task(FS_dir: str, output_path: Path):
    t1_FSpath = os.path.join(FS_dir, "mri", "T1.mgz")
    t1brain_FSpath = os.path.join(FS_dir, "mri", "brainmask.mgz")
    wmseg_FSpath = os.path.join(FS_dir, "mri", "wm.seg.mgz")
    normimg_FSpath = os.path.join(FS_dir, "mri", "T1.mgz")

    return t1_FSpath, t1brain_FSpath, wmseg_FSpath, normimg_FSpath


wf.add(join_task(FS_dir=wf.lzin.FS_dir, name="join_task"))

# need to convert .mgz to nifti for registration
wf.add(
    MrConvert(
        in_file=wf.join_task.lzout.t1_FSpath,
        out_file="t1.nii.gz",
        name="nifti_t1",
    )
)

wf.add(
    MrConvert(
        in_file=wf.join_task.lzout.t1brain_FSpath,
        out_file="t1brain.nii.gz",
        name="nifti_t1brain",
    )
)

wf.add(
    MrConvert(
        in_file=wf.join_task.lzout.wmseg_FSpath,
        out_file="wmseg.nii.gz",
        name="nifti_wmseg",
    )
)

wf.add(
    MrConvert(
        in_file=wf.join_task.lzout.normimg_FSpath,
        out_file="normimg.nii.gz",
        name="nifti_normimg",
    )
)

# extract meanb0 volumes #

wf.add(
    DwiExtract(
        in_file=wf.lzin.dwi_preproc_mif,
        out_file="bzero.mif.gz",
        bzero=True,
        name="extract_bzeroes_task",
    )
)

# mrcalc spec info
mrcalc_max_input_spec = SpecInfo(
    name="Input",
    fields=[
        (
            "in_file",
            ImageIn,
            {
                "help_string": "path to input image 1",
                "argstr": "{in_file}",
                "mandatory": True,
                "position": -4,
            },
        ),
        (
            "number",
            str,
            {
                "help_string": "minimum value",
                "argstr": "{number}",
                "mandatory": True,
                "position": -3,
            },
        ),
        (
            "operand",
            str,
            {
                "help_string": "operand to execute",
                "mandatory": True,
                "position": -2,
                "argstr": "-{operand}",
            },
        ),
        (
            "output_image",
            Path,
            {
                "help_string": "path to output image",
                "output_file_template": "mrcalc_output_image.nii.gz",
                "argstr": "",
                # "mandatory": True,
                "position": -1,
            },
        ),
        (
            "datatype",
            str,
            {
                "help_string": "datatype option",
                "argstr": "-datatype {datatype}",
                "position": -5,
            },
        ),
    ],
    bases=(ShellSpec,),
)

mrcalc_output_spec = SpecInfo(
    name="Output",
    fields=[
        (
            "output_image",
            ImageOut,
            {
                "help_string": "path to output image",
                "mandatory": False,
                "output_file_template": "mrcalc_output_image.nii.gz",
                "position": -1,
            },
        ),
    ],
    bases=(ShellOutSpec,),
)

# remove negative values from bzero volumes
wf.add(
    ShellCommandTask(
        name="mrcalc_max",
        executable="mrcalc",
        input_spec=mrcalc_max_input_spec,
        output_spec=mrcalc_output_spec,
        # cache_dir=output_path,
        in_file=wf.extract_bzeroes_task.lzout.out_file,
        output_image="b0_nonneg.mif.gz",
        number="0.0",
        operand="max",
    )
)

# # create meanb0 image
wf.add(
    MrMath(
        in_file=wf.mrcalc_max.lzout.output_image,
        out_file="dwi_meanbzero.nii.gz",
        name="meanb0_task",
        operation="mean",
        axis=3,
    )
)

# make wm mask a binary image
wf.add(
    ShellCommandTask(
        name="mrcalc_wmbin",
        executable="mrcalc",
        input_spec=mrcalc_max_input_spec,
        output_spec=mrcalc_output_spec,
        cache_dir=output_path,
        in_file=wf.nifti_wmseg.lzout.out_file,
        number="0",
        operand="gt",
    )
)

# Step 9: Perform DWI->T1 registration
wf.add(
    EpiReg(
        epi=wf.meanb0_task.lzout.out_file,
        t1_head=wf.nifti_normimg.lzout.out_file,
        t1_brain=wf.nifti_t1brain.lzout.out_file,
        wmseg=wf.mrcalc_wmbin.lzout.output_image,
        out_base="epi2struct",
        name="epi_reg_task",
        matrix="epi2struct.mat",
    )
)

# # transformconvert task
wf.add(
    TransformConvert(
        input=wf.epi_reg_task.lzout.matrix,
        operation="flirt_import",
        flirt_in=wf.meanb0_task.lzout.out_file,
        flirt_ref=wf.nifti_t1brain.lzout.out_file,
        out_file="epi2struct_mrtrix.txt",
        name="transformconvert_task",
    )
)

# Step 10: Apply transform (to get DWI images in T1 space)
wf.add(
    MrTransform(
        name="transformDWI_task",
        in_file=wf.lzin.dwi_preproc_mif,
        inverse=False,
        out_file="DWI_registered.mif.gz",
        linear=wf.transformconvert_task.lzout.out_file,
        strides=wf.nifti_normimg.lzout.out_file,
    )
)

wf.add(
    MrTransform(
        name="transformDWImask_task",
        in_file=wf.lzin.dwi_mask_mif,
        inverse=False,
        out_file="DWImask_registered.mif.gz",
        linear=wf.transformconvert_task.lzout.out_file,
        strides=wf.nifti_normimg.lzout.out_file,
    )
)

# # # # ##################################
# # # # # Tractography preparation steps #
# # # # ##################################

# Generate FOD (feed group-averaged response function as an input)
wf.add(
    Dwi2Fod(
        name="GenFod_task",
        algorithm="msmt_csd",
        dwi=wf.transformDWI_task.lzout.out_file,
        mask=wf.transformDWImask_task.lzout.out_file,
        response_odf_wm=wf.lzin.avg_respfcn_WM,
        response_odf_gm=wf.lzin.avg_respfcn_GM,
        response_odf_csf=wf.lzin.avg_respfcn_CSF,
    )
)

# Normalise FOD
wf.add(
    MtNormalise(
        name="NormFod_task",
        mask=wf.crop_task_mask.lzout.out_file,
        fod_wm=wf.GenFod_task.lzout.fod_wm,
        fod_gm=wf.GenFod_task.lzout.fod_gm,
        fod_csf=wf.GenFod_task.lzout.fod_csf,
        # fod_wm_norm="wmfodnorm.mif",
    )
)

# Tractography
wf.add(
    TckGen(
        name="tckgen_task",
        in_file=wf.NormFod_task.lzout.fod_wm_norm,
        # tracks="tractogram.tck",
        algorithm="ifod2",
        select=1000,
        minlength=5.0,
        maxlength=350.0,
        seed_dynamic=wf.NormFod_task.lzout.fod_wm_norm,
        act=wf.lzin.fTT_image_T1space,
        backtrack=True,
        crop_at_gmwmi=True,
        cutoff=0.06,
        seeds=0,
    )
)

# SIFT2
wf.add(
    TckSift2(
        name="SIF2_task",
        in_tracks=wf.tckgen_task.lzout.tracks,
        in_fod=wf.NormFod_task.lzout.fod_wm_norm,
        act=wf.lzin.fTT_image_T1space,
        out_mu="mu.txt",
    )
)

################
# CONNECTOMICS #
################
wf.add(
    Tck2Connectome(
        name="connectomics_task",
        in_tracks=wf.tckgen_task.lzout.tracks,
        tck_weights_in=wf.SIF2_task.lzout.out_weights,
        nodes_in=wf.transformParcellation_task.lzout.out_file,
        symmetric=True,
        zero_diagonal=True,
    )
)

# ############
# # TDI maps #
# ############

wf.add(
    TckMap(
        name="TDImap_task",
        in_tracks=wf.tckgen_task.lzout.tracks,
        tck_weights_in=wf.SIF2_task.lzout.out_weights,
        vox=0.2,
        template=wf.transform5TT_task.lzout.out_file,
        out_file="TDI.mif.gz",
    )
)

wf.add(
    TckMap(
        name="DECTDImap_task",
        in_tracks=wf.tckgen_task.lzout.tracks,
        tck_weights_in=wf.SIF2_task.lzout.out_weights,
        vox=0.2,
        template=wf.transform5TT_task.lzout.out_file,
        dec=True,
        out_file="DECTDI.mif.gz",
    )
)


# # SET WF OUTPUT
wf.set_output(("sift_mu", wf.SIF2_task.lzout.out_mu))
wf.set_output(("sift_weights", wf.SIF2_task.lzout.out_weights))
wf.set_output(("wm_fod_norm", wf.NormFod_task.lzout.fod_wm_norm))
wf.set_output(("conenctome_file", wf.connectomics_task.lzout.connectome_out))
wf.set_output(("TDI_file", wf.TDImap_task.lzout.out_file))
wf.set_output(("DECTDI_file", wf.DECTDImap_task.lzout.out_file))
wf.set_output(("tractogram", wf.tckgen_task.lzout.tracks))

# wf.set_output(("tform", wf.transformconvert_task.lzout.out_file))
# wf.set_output(("epireg", wf.epi_reg_task.lzout.matrix))

# ########################
# # Execute the workflow #
# ########################

result = wf(
    dwi_preproc_mif="/Users/arkievdsouza/Desktop/ConnectomeBids/sub-01_DWI.mif.gz",
    FS_dir="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/Fastsurfer_b5d77a6efac5b7efedbd561a717bdbc6/subjects_dir/FS_outputs/",
    fTT_image_T1space="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/5TT_hsvs.mif.gz",
    parcellation_image_T1space="/Users/arkievdsouza/git/t1-pipeline/working-dir/T1_pipeline_v3_testing/sub-01-T1w_pos_FULLPIPE/Atlas_desikan.mif.gz",
    avg_respfcn_WM="/Users/arkievdsouza/Desktop/ConnectomeBids/sub-01_tissue-WM_response.txt",
    avg_respfcn_GM="/Users/arkievdsouza/Desktop/ConnectomeBids/sub-01_tissue-GM_response.txt",
    avg_respfcn_CSF="/Users/arkievdsouza/Desktop/ConnectomeBids/sub-01_tissue-CSF_response.txt",
    plugin="serial",
)
