#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import logging

from flask import Flask
from flask import request, render_template, url_for, abort, jsonify
from flask.ext.analytics import Analytics

from reliure.utils.log import get_basic_logger
from reliure.web import RemoteApi, app_routes

from tmuseapi import TmuseApi
import wiktionary as wk


# Build the app & 
app = Flask(__name__)
app.debug = os.environ['DEBUG'] == "true"
logger = get_basic_logger(logging.DEBUG)

# ajout la config pour le tracker Piwik
if not app.debug:
    app.config["PIWIK_BASEURL"] = "stats.kodexlab.com"
    app.config["PIWIK_SITEID"] = 8
Analytics(app)

import requests_cache
requests_cache.install_cache('../cache/demo_cache.sqlite')

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
         debug=app.debug,
         root_url=url_for("index"),
         complete_url=url_for("%s.complete" % tmuseApi.name),
         engine_url=url_for("%s.subgraph" % tmuseApi.name),
         random_url=url_for("%s.random_node" % tmuseApi.name),
         def_url=url_for("wkdef", domain="", query="")[:-1] # rm trailing /
    )

@app.route("/def/<string:domain>/<string:query>")
def wkdef(domain, query):
    """ get and parse definition from wiktionary
        @returns html code of the definition
    """
    pos_headers = { 'A':'Adjectif', 'N':'Nom_commun', 'V':'Verbe', 'E':'Adverbe'}

    data = {}
    try :
        pos = [ request.args.get('pos', None) ]
        allowed = [ pos_headers.get(p, None) for p in pos ]
        allowed = tuple( x for x in allowed if x is not None )
        data = wk.get_wk_definition(domain, query.encode('utf8'), allowed=allowed)
    except:
        raise
        resp = "<table><tr><td><img src='../static/images/warning.png'/></td><td>" + \
        "can't get definition from <a href='"+query+"' target='_blank'>"+query+"</a>" + \
        "</td></tr></table>"

        data = { 
            'content' : resp,
            #'error' : error.message
        }

    return jsonify(data)


def main():
    ## run the app
    from flask.ext.runner import Runner
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())


