#!/bin/bash
source "$(dirname $0)/config.sh"

# Four minutes of timeout: if the catapult is in use, it might take some time
# for jobs to complete to make room to respond to ping.
TIMEOUT=240

echo "\$PATH: $PATH"

cd $CATAPULT_DIR

diff <(timeout $TIMEOUT ./catalaunch $BUILDS_DIR/pipeline.sock PING) <(echo -n PONG)

ok=$?

echo "OK: " $ok

if [ $ok -ne 0 ]
then
    date; echo "RESTARING!"
    pkill -f "catapult.py"
    ./start-server.sh
fi

