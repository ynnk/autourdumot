#!/bin/bash
## Run  through gunicorn

#set -x  #log all execed lin for debug
set -e
BASEDIR=/var/wwwapps/autourdumot
APPMODULE=autourdumot
APPNAME=app

# log
LOGFILE=$BASEDIR/log/autourdumot.log
LOGDIR=$(dirname $LOGFILE)
LOGLEVEL="info"

# gunicorn config
BIND=0.0.0.0:8125
NUM_WORKERS=1

# user/group to run as
USER=wwwapps
GROUP=wwwapps

## start the app
cd $BASEDIR
# if  virtualenv is used 
source venv/bin/activate

#pre-start script
# create log dir if not exist
test -d $LOGDIR || mkdir -p $LOGDIR
#end script

# mv into app dir
export PYTHONPATH=$BASEDIR
cd app

# set Elastic Search host
export ES_HOST="localhost:9200"
export ES_INDEX="autourdumot"
export APP_DEBUG=false

# run the gunicorn server
exec gunicorn --workers $NUM_WORKERS --bind=$BIND\
    --user=$USER --group=$GROUP --log-level=$LOGLEVEL \
    --log-file=$LOGFILE $APPMODULE:$APPNAME #2>>$LOGFILE
