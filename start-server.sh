#!/bin/bash
source config.sh

export PYTHONPATH=$SPARV_PYTHON${PYTHONPATH:+:$PYTHONPATH}
export PATH=$SPARV_BIN:/usr/local/cwb-3.4.5/bin:/usr/local/bin:${HOME}/.local/bin:$PATH
export SPARV_MODELS=$SPARV_MODELS

SALDO_MODEL=$SPARV_MODELS/saldo.pickle
DALIN_MODEL=$SPARV_MODELS/dalin.pickle
SWEDBERG_MODEL=$SPARV_MODELS/swedberg.pickle
SALDO_COMPOUND_MODEL=$SPARV_MODELS/saldo.compound.pickle
STATISTIC_MODEL=$SPARV_MODELS/stats.pickle

MALT_JAR=$SPARV_BIN/maltparser-1.7.2/maltparser-1.7.2.jar
MALT_MODEL=$SPARV_MODELS/swemalt-1.7.2.mco

PROCESSES=1
VERBOSE=true

mkdir -p $BUILDS_DIR -m 777 -v
cp $SPARV_MAKEFILES/Makefile.rules $BUILDS_DIR -v
cp $SPARV_MAKEFILES/Makefile.config $BUILDS_DIR -v
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

# Adapted to be run with Supervisord
wait -n
