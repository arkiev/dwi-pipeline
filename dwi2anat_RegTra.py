from pydra import Workflow, ShellCommandTask
from pydra.engine.specs import File, SpecInfo, ShellSpec, ShellOutSpec
from pathlib import Path

# Define paths
output_path = Path("/Users/arkievdsouza/git/dwi-pipeline/working-dir/")

# Define input and output specifications
input_spec = {
    "meanB0_brain": File,
    "anat_brain": File,
}

output_spec = {
    "warped_image": File,
    "inversewarped_image": File,
}

# Create the workflow
wf = Workflow(
    name="RegTra_ANTs_wf",
    input_spec=input_spec,
    cache_dir=output_path,
    output_spec=output_spec,
)

# ANTs Registration specifications
ANTsReg_input_spec = SpecInfo(
    name="Input",
    fields=[
        (
            "anat_image",
            File,
            {
                "help_string": "Path to input anatomical image",
                "argstr": "-f {anat_image}",
                "mandatory": True,
            },
        ),
        (
            "meanb0_image",
            File,
            {
                "help_string": "Path to input meanb0 image",
                "argstr": "-m {meanb0_image}",
                "mandatory": True,
            },
        ),
        (
            "image_dimensions",
            int,
            {
                "help_string": "Image dimensions (2 or 3)",
                "argstr": "-d {image_dimensions}",
                "mandatory": True,
            },
        ),
        (
            "threads",
            int,
            {
                "help_string": "Number of threads",
                "argstr": "-o {threads}",
                "mandatory": True,
            },
        ),
        (
            "OutputPrefix",
            str,
            {
                "help_string": "Output prefix",
                "argstr": "-o {OutputPrefix}",
                "output_file_template": "ANTs_output_",
            },
        ),
    ],
    bases=(ShellSpec,),
)


def warped_path(str):
    return str("ANTs_output_Warped.nii.gz")


def invwarped_path(str):
    return str("ANTs_output_InverseWarped.nii.gz")


ANTsReg_output_spec = SpecInfo(
    name="Output",
    fields=[
        (
            "warped_image",
            File,
            {
                "help_string": "Warped image",
                "output_file_template": "ANTs_output_Warped.nii.gz",
            },
        ),
        (
            "inverse_warped_image",
            File,
            {
                "help_string": "Inverse warped image",
                "output_file_template": "ANTs_output_InverseWarped.nii.gz",
            },
        ),
    ],
    bases=(ShellOutSpec,),
)

# Add the ANTs registration task
wf.add(
    ShellCommandTask(
        name="ANTsReg_task",
        executable="antsRegistrationSyN.sh",
        input_spec=ANTsReg_input_spec,
        output_spec=ANTsReg_output_spec,
        anat_image=wf.lzin.anat_brain,
        meanb0_image=wf.lzin.meanB0_brain,
        threads=24,
        image_dimensions=3,
        OutputPrefix="ANTs_output_",  # Ensure this prefix matches with your output file templates
    )
)

# Set the output
wf.set_output(("warped_image", wf.ANTsReg_task.lzout.warped_image))
wf.set_output(("inversewarped_image", wf.ANTsReg_task.lzout.inverse_warped_image))

# Execute the workflow
result = wf(
    meanB0_brain="/Users/arkievdsouza/Desktop/data/temp_B0img.nii.gz",
    anat_brain="/Users/arkievdsouza/Desktop/data/T1brain.nii.gz",
    plugin="serial",
)
