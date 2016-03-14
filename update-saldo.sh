#!/bin/bash
source config.sh

export PYTHONPATH=$SB_PYTHON${PYTHONPATH:+:$PYTHONPATH}

cd $SB_MODELS

make clean
make all

# Kill the catapult: keep-alive.sh cronjob will resurrect it
pkill -f "catapult.py"

