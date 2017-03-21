#!/bin/bash

# BACKEND and PIPELINE are not needed by the catapult
BACKEND="/export/htdocs_sbws/ws/sparv/v1"
PIPELINE="${BACKEND}/pipeline"

### The remaining variables must be set! ###
# paths to modules, models and makefiles in the pipeline
SPARV_PYTHON="${PIPELINE}/python"
SPARV_MODELS="${PIPELINE}/models"
SPARV_BIN="${PIPELINE}/bin"
SPARV_MAKEFILES="${PIPELINE}/makefiles"

# catapult and builds directory
CATAPULT_DIR="${HOME}/catapult"
BUILDS_DIR="${BACKEND}/builds"
