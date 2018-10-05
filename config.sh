#!/bin/bash

# BACKEND and PIPELINE are not needed by the catapult (only whithin this file)
BACKEND="${HOME}/sparv/backend"
PIPELINE="${BACKEND}/data/sparv-pipeline"

### The remaining variables must be set! ###
# paths to modules, models and makefiles in the pipeline
SPARV_PYTHON="${PIPELINE}"
SPARV_MODELS="${PIPELINE}/models"
SPARV_BIN="${PIPELINE}/bin"
SPARV_MAKEFILES="${PIPELINE}/makefiles"

# catapult, builds and log directory
CATAPULT_DIR="${BACKEND}/sparv-catapult"
BUILDS_DIR="${BACKEND}/data/builds"
LOGDIR="${BACKEND}/logs"

# Path to virtualenv, optional
CATAPULT_VENV="${CATAPULT_DIR}/venv"
