#!/bin/bash
set -e

if [ -e "/var/opt/morpheus/vm/morpheus.env" ]; then
	source /var/opt/morpheus/vm/morpheus.env
fi

export JVM_MIN_MEM='64m'
export JVM_MAX_MEM='64m'
export CONFIG_HOME=/morpheus/config
export APP_HOME=/morpheus/data
export LOGS_HOME=/morpheus/logs

if [[ ! -e $CONFIG_HOME/startup.txt ]]; then
	cp /startup.txt $CONFIG_HOME/
fi

files=$(ls $APP_HOME/*.jar 2> /dev/null | wc -l)
if [ "$files" = "0" ]; then
   cp /app.jar $APP_HOME/
fi

cd /morpheus/data
export JAVA_STARTUP=`cat /morpheus/config/startup.txt`

exec java -Xms$JVM_MIN_MEM -Xmx$JVM_MAX_MEM  $JAVA_STARTUP > $LOGS_HOME/app.log
