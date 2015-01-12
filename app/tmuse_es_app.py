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
from reliure.utils.web import ReliureFlaskView, EngineView, RemoteApi

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

# Configure the app

ES_HOST = os.environ.get('ES_HOST', "localhost:9200")
ES_INDEX = os.environ.get('ES_INDEX', "tmuse")


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

class TmuseApi(ReliureFlaskView):

    def __init__(self, name, index, ):
        """ Api over tmuse es
        """
        assert index._es.ping(), "impossible to reach ES server"
        
        super(TmuseApi, self).__init__( url_prefix = "/%s" % name )

        self.name = name
        self.index = index
        # build the API from this engine
        engineapi = EngineView(tmuse.engine(index))
        engineapi.set_input_type(ComplexQuery())
        engineapi.add_output("query", ComplexQuery.serialize)
        engineapi.add_output("graph", export_graph)
        engineapi.add_output("layout", export_layout)
        engineapi.add_output("clusters", export_clustering)

        self.add_engine("subgraph", engineapi)
        
        # add another route for completion
        self.add_url_rule("/complete/<string:text>", 'complete', self.complete,  methods=["GET"])

    def repr(self):
        return self.name
    
    def complete(self, text):
        response = { 'length':0 }
        text = text or ""
        while len(text) and response['length'] == 0 :
            response = tmuse.complete(self.index, text)
            text = text[:-1]
        return jsonify( response )

app.es_index = EsIndex(ES_INDEX, doc_type="graph", host=ES_HOST)

# remote api
# app.api = RemoteEngineApi("http://ollienary:8044/api")

# locale api
app.api = TmuseApi("tmuse_v1", app.es_index)

app.register_blueprint(app.api)




# index page
@app.route("/")
@app.route("/<string:query>")
def index(query=None):
    t = request.args.get("t","")
    tmpl = "index%s%s.html" % ( "_" if len(t) else "", t)
    tmpl = "index_nav.html"
    return render_template(tmpl, root_url=url_for("index"),
                                 def_url= url_for("wkdef", domain="", query="")[:-1], # rm trailing /
                                 engine_url= url_for("%s.subgraph" % app.api.name),
                                 complete_url= url_for("ajax_complete"))


@app.route("/ajax_complete")
def ajax_complete():
    print request.args
    terms = [ request.args.get(e,"") for e in ('lang', 'pos', 'form') ]
    term = ".".join( t for t in terms if t != "" )
    return app.api.call('complete', term)
 
@app.route("/def/<string:domain>/<string:query>")
def wkdef(domain, query):
    """ get and parse definition from wiktionary
        @returns html code of the definition
    """
    data = {}
    try : 

        data = wiktionary.get_wk_definition(domain, query)

    except Exception as error:

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

@app.route("/routes")
def routes():
    #for rule in app.url_map.iter_rules():
    _routes = []
    for rule in app.url_map.iter_rules() :
        _routes.append( ( rule.rule, rule.endpoint, list(rule.methods) ) )
    return jsonify({ 'routes': _routes })



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

def main():
    ## run the app
    from flask.ext.runner import Runner
    
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())


