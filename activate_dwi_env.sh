#!/bin/bash
# Activation script for DWI preprocessing pipeline environment

# Define the virtual environment path
VENV_PATH="$HOME/dwi_pipeline_env"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Creating new virtual environment..."
    python3 -m venv "$VENV_PATH"
    
    # Activate the environment
    source "$VENV_PATH/bin/activate"
    
    echo "Installing required packages..."
    pip install --upgrade pip
    pip install pydra
    pip install attrs
    pip install fileformats
    pip install fileformats-medimage
    pip install fileformats-medimage-mrtrix3
    pip install pydra-mrtrix3
    pip install pydra-fastsurfer
    pip install pydra-fsl
    
    echo ""
    echo "=========================================="
    echo "Environment setup complete!"
    echo "=========================================="
    echo ""
    echo "NOTE: Your script has a naming issue on line 80:"
    echo "  - Line 18 imports: dwidenoise (lowercase)"
    echo "  - Line 80 uses: DwiDenoise (capitalized)"
    echo "You'll need to change line 80 to use 'dwidenoise' instead."
    echo ""
else
    # Activate existing environment
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated: $VENV_PATH"
fi

# Display Python version and location
echo "Python: $(which python)"
echo "Python version: $(python --version)"
