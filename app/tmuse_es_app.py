#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import json
import logging
import igraph

from flask import Flask
from flask import render_template, url_for, abort, jsonify

from cello.types import GenericType, Text, Numeric
from cello.graphs import export_graph, IN, OUT, ALL
from cello.layout import export_layout
from cello.clustering import export_clustering
from cello.utils.log import get_basic_logger
from cello.providers.es import EsIndex
from cello.utils.web import CelloFlaskView

import tmuse


# Build the app & 
app = Flask(__name__)
app.debug = True
logger = get_basic_logger(logging.DEBUG)

class ComplexQuery(GenericType):
    def parse(self, value):
        return value


def tmuse_api(index, *args, **kwargs):
    """ Build the Cello/Naviprox API over a graph
    """
    # use default engine in cello_guardian.py
    engine = tmuse.engine(index, *args, **kwargs)

    # build the API from this engine
    api = CelloFlaskView(engine)
    api.set_input_type(ComplexQuery())
    api.add_output("query", lambda x : { k:v.encode('utf8') for k,v in x.iteritems()} )
    api.add_output("graph", export_graph)
    api.add_output("layout", export_layout)
    api.add_output("clusters", export_clustering)
    return api

# index page
@app.route("/")
@app.route("/<string:query>")
def index(query=None):
    root_url = url_for("index")
    return render_template('index.html', root_url=root_url)

@app.route("/complete/<string:text>")
def complete(text):
    es_res = tmuse.complete(app.es_index, text)
    return jsonify( es_res )

@app.route("/extract/<string:graph>/<string:text>")
def test(graph, text):
    es_res = tmuse.extract(app.es_index, graph, text)
    return jsonify({ 'res': es_res})
    
def main():
    INDEX = "tmuse"
    #INDEX = "test"
    app.graphs = {"dicosyn.V", }
    app.es_index = EsIndex(INDEX, doc_type="graph", host="localhost" )

    api = tmuse_api(app.es_index)
    app.register_blueprint(api, url_prefix="/api" )

    app.run("0.0.0.0")

if __name__ == '__main__':
    sys.exit(main())


