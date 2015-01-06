#!/bin/bash
## Run  through gunicorn

#set -x  #log all execed lin for debug
set -e
BASEDIR=/var/wwwapps/tmuse_alpha_v2/tmuse
APPMODULE=tmuse_es_app
APPNAME=app

# log
LOGFILE=$BASEDIR/log/tmuse.log
LOGDIR=$(dirname $LOGFILE)
LOGLEVEL=debug

# gunicorn config
BIND=0.0.0.0:8051
NUM_WORKERS=1

# user/group to run as
USER=wapps
GROUP=wapps

## start the app
cd $BASEDIR
# if  virtualenv is used 
source ../venv/bin/activate

#pre-start script
# create log dir if not exist
test -d $LOGDIR || mkdir -p $LOGDIR
#end script

# mv into app dir
cd app

# set Elastic Search host
export ES_HOST=192.168.122.90:9200


# run the gunicorn server
exec gunicorn --workers $NUM_WORKERS --bind=$BIND\
    --user=$USER --group=$GROUP --log-level=$LOGLEVEL \
    --log-file=$LOGFILE $APPMODULE:$APPNAME #2>>$LOGFILE
