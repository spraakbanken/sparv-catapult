#!/bin/bash
source config.sh

export PYTHONPATH=$SB_PYTHON${PYTHONPATH:+:$PYTHONPATH}
export PATH=$SB_BIN:/usr/local/cwb-3.4.5/bin:/usr/local/bin:$PATH
export SB_MODELS=$SB_MODELS

SALDO_MODEL=$SB_MODELS/saldo.pickle
DALIN_MODEL=$SB_MODELS/dalin.pickle
SWEDBERG_MODEL=$SB_MODELS/swedberg.pickle
SALDO_COMPOUND_MODEL=$SB_MODELS/saldo.compound.pickle
STATISTIC_MODEL=$SB_MODELS/stats.pickle

MALT_JAR=$SB_BIN/maltparser-1.7.2/maltparser-1.7.2.jar
MALT_MODEL=$SB_MODELS/swemalt-1.7.2.mco

PROCESSES=1
VERBOSE=true

mkdir -p $BUILDS_DIR -m 777 -v
cp $CATAPULT_DIR/Makefile* $BUILDS_DIR -v
cp $CATAPULT_DIR/catalaunch $BUILDS_DIR -v
chmod 755 $BUILDS_DIR/catalaunch -v

PIPELINE_SOCK=$BUILDS_DIR/pipeline.sock
rm -fv $PIPELINE_SOCK

echo "Starting catapult on socket $PIPELINE_SOCK in background"
python $CATAPULT_DIR/catapult.py \
    --socket_path $PIPELINE_SOCK \
    --processes $PROCESSES \
    --saldo_model $SALDO_MODEL \
    --dalin_model $DALIN_MODEL \
    --swedberg_model $SWEDBERG_MODEL \
    --malt_jar $MALT_JAR \
    --malt_model $MALT_MODEL \
    --compound_model $SALDO_COMPOUND_MODEL \
    --stats_model $STATISTIC_MODEL \
    --verbose $VERBOSE &> $BUILDS_DIR/catalog &
echo "Catapult pid: $!"

# Waiting for socket to get created
inotifywait -e create $BUILDS_DIR
chmod 777 $PIPELINE_SOCK -v
