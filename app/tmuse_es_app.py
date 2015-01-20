#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import logging

from flask import Flask
from flask import request, render_template, url_for, abort, jsonify

from reliure.utils.log import get_basic_logger

from reliure.web import RemoteApi, app_routes
from tmuseapi import TmuseApi
import wiktionary


# Build the app & 
app = Flask(__name__)
app.debug = True
logger = get_basic_logger(logging.DEBUG)


# remote api
#tmuseApi = RemoteApi("http://carton.kodexlab.com/tmuse_alpha/tmuse_v1")
#tmuseApi = RemoteApi("http://localhost:5123/tmuse_v1", url_prefix="")

# locale api
ES_HOST = os.environ.get('ES_HOST', "localhost:9200")
ES_INDEX = os.environ.get('ES_INDEX', "tmuse")
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE', "graph")

tmuseApi = TmuseApi("tmuse_v1", ES_HOST, ES_INDEX, ES_DOC_TYPE)

# Configure the app
app.register_blueprint(tmuseApi)

app.add_url_rule('/_routes', 'routes', lambda : app_routes(app) ,  methods=["GET"])


# index page
@app.route("/")
@app.route("/<string:query>")
def index(query=None):
    return render_template(
         "index_nav.html",
         root_url=url_for("index"),
         complete_url=url_for("%s.complete" % tmuseApi.name),
         engine_url=url_for("%s.subgraph" % tmuseApi.name),
         def_url=url_for("wkdef", domain="", query="")[:-1] # rm trailing /
    )

@app.route("/def/<string:domain>/<string:query>")
def wkdef(domain, query):
    """ get and parse definition from wiktionary
        @returns html code of the definition
    """
    data = {}
    try : 
        data = wiktionary.get_wk_definition(domain, query.encode('utf8'))
    except :
        resp = "<table><tr><td><img src='../static/images/warning.png'/></td><td>" + \
        "can't get definition from <a href='"+url+"' target='_blank'>"+url+"</a>" + \
        "</td></tr></table>"

        data = { 
            'content' : resp,
            'error' : error.message
        }
    finally :
        return jsonify(data)


def main():
    ## run the app
    from flask.ext.runner import Runner
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())


