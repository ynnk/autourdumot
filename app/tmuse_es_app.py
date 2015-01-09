#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import json
import logging
import igraph

from flask import Flask
from flask import request, render_template, url_for, abort, jsonify

from reliure.types import GenericType, Text, Numeric
from reliure.utils.log import get_basic_logger
from reliure.utils.web import ReliureFlaskView

from cello.graphs import export_graph, IN, OUT, ALL
from cello.layout import export_layout
from cello.clustering import export_clustering
from cello.providers.es import EsIndex

import tmuse
import wiktionary

# Build the app & 
app = Flask(__name__)
app.debug = True
logger = get_basic_logger(logging.DEBUG)

class ComplexQuery(GenericType):
    def parse(self, value):
        q = [ Query(**{ k:v for k,v in val.iteritems() if v is not None}) for val in value ]
        
        logger.info( "ComplexeQuery %s" % q )
        return q
    @staticmethod
    def serialize(complexquery):
        uri = ",".join([  '.'.join( ( q['lang'], q['pos'], q['form'] ) ) for q in complexquery ])
        return {'units': complexquery,
                'uri'  : uri  
               }

def Query( **kwargs):
    default = {
        'lang'  : 'fr',
        'pos'   : 'V',
        'form'  : None
    }
    default.update(kwargs)
    default['graph'] = 'jdm.%s.flat' % default['pos']
    return default

def tmuse_api(index, *args, **kwargs):
    """ Build the Cello/Naviprox API over a graph
    """
    # use default engine in cello_guardian.py
    engine = tmuse.engine(index, *args, **kwargs)

    # build the API from this engine
    api = ReliureFlaskView(engine)
    api.set_input_type(ComplexQuery())
    api.add_output("query", ComplexQuery.serialize)
    api.add_output("graph", export_graph)
    api.add_output("layout", export_layout)
    api.add_output("clusters", export_clustering)
    return api

# index page
@app.route("/")
@app.route("/<string:query>")
def index(query=None):
    t = request.args.get("t","")
    tmpl = "index%s%s.html" % ( "_" if len(t) else "", t)
    tmpl = "index_nav.html"
    root_url = url_for("index")
    return render_template(tmpl, root_url=root_url)

@app.route("/complete/<string:text>")
def complete(text):
    logger.info( "complete: %s" % text )
    response = { 'length':0 }
    _text = text or ""
    while len(_text) and response['length'] == 0 :
        response = tmuse.complete(app.es_index, _text)
        _text = _text[:-1]
    return jsonify( response )

@app.route("/ajax_complete")
def ajax_complete():
    print request.args
    terms = [ request.args.get(e,"") for e in ('lang', 'pos', 'form') ]
    term = ".".join( t for t in terms if t != "" )
    return complete(term)
 
@app.route("/def/<string:domain>/<string:query>")
def wkdef(domain, query):
    """ get and parse definition from wiktionary
        @returns html code of the definition
    """
    data = {}
    try : 

        data = wiktionary.get_wk_definition(domain, query)
        
    except Exception as error:

        print "errorrr" , error

        resp = "<table><tr><td><img src='../static/images/warning.png'/></td><td>" + \
        "can't get definition from <a href='"+url+"' target='_blank'>"+url+"</a>" + \
        "</td></tr></table>"

        data = { 
            'content' : resp,
            'error' : error.message
        }

    finally :
        return jsonify(data)


# debug

@app.route("/_extract/<string:graph>/<string:text>")
def _extract(graph, text):

    query = Query(graph=graph, form=text)     
    es_res = tmuse.extract(app.es_index, query)
    return jsonify({ 'res': es_res})
    
@app.route("/_prox/<string:graph>/<string:text>")
def _prox(graph, text):
    
    query = Query(graph=graph, form=text)     

    proxs = dict(tmuse.extract(app.es_index, query, 10))
    ids = proxs.keys()
    # request es with ids
    es_res = tmuse.search_docs(app.es_index, graph, ids)
    return jsonify({ 'ids': ids, 'res': es_res})

# Configure the app

ES_HOST = os.environ.get('ES_HOST', "localhost:9200")
ES_INDEX = os.environ.get('ES_INDEX', "tmuse")

app.es_index = EsIndex(ES_INDEX, doc_type="graph", host=ES_HOST)
assert app.es_index._es.ping(), "impossible to reach ES server"

api = tmuse_api(app.es_index)
app.register_blueprint(api, url_prefix="/api")

def main():
    ## run the app
    from flask.ext.runner import Runner
    
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())


