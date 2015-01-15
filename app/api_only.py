#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import logging

from flask import Flask
from flask import request, render_template, url_for, abort, jsonify

from reliure.utils.log import get_basic_logger

from reliure.utils.web import RemoteApi, app_routes
from tmuseapi import TmuseApi
import wiktionary


# Build the app & 
app = Flask(__name__)
app.debug = True
logger = get_basic_logger(logging.DEBUG)


# remote api
#tmuseApi = RemoteApi("http://carton.kodexlab.com/tmuse_alpha/tmuse_v1")

# locale api
ES_HOST = os.environ.get('ES_HOST', "localhost:9200")
ES_INDEX = os.environ.get('ES_INDEX', "tmuse")
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE', "graph")

tmuseApi = TmuseApi("tmuse_v1", ES_HOST, ES_INDEX, ES_DOC_TYPE)

# Configure the app
app.register_blueprint(tmuseApi)

app.run("0.0.0.0",5123, debug=True)