#!/bin/bash

# BACKEND and PIPELINE are not needed by the catapult
BACKEND="/export/htdocs_sbws/ws/sparv/v1"
PIPELINE="${BACKEND}/pipeline"

### The remaining variables must be set! ###
# paths to modules and models in the pipeline
SB_PYTHON="${PIPELINE}/python"
SB_MODELS="${PIPELINE}/models"
SB_BIN="${PIPELINE}/bin"

# paths to makefiles needed by the pipeline
SB_MAKEFILES="${HOME}/makefiles"

# catapult and builds directory
CATAPULT_DIR="${HOME}/catapult"
BUILDS_DIR="${BACKEND}/builds"
