#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import request, jsonify

from reliure.types import GenericType, Text, Numeric
from reliure.utils.web import ReliureBlue, EngineView, RemoteApi
from reliure.pipeline import Optionable, Composable

from cello.graphs import export_graph, IN, OUT, ALL
from cello.layout import export_layout
from cello.clustering import export_clustering
from cello.providers.es import EsIndex

import tmuse


class ComplexQuery(GenericType):
    def parse(self, value):
        q = [ Query(**{ k:v for k,v in val.iteritems() if v is not None}) for val in value ]
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

def TmuseApi( name, host='localhost:9200', index_name='tmuse', doc_type='graph'):
        """ Api over tmuse es
        """
        esindex = EsIndex(index_name, doc_type=doc_type , host=host)
        assert esindex._es.ping(), "impossible to reach ES server"

        # build the API from this engine
        print "api name", name
        api = ReliureBlue(name, expose_route=True, url_prefix="/%s" % name)
        
        view = EngineView(engine(esindex))
        view.set_input_type(ComplexQuery())
        view.add_output("query", ComplexQuery.serialize)
        view.add_output("graph", export_graph)
        view.add_output("layout", export_layout)
        view.add_output("clusters", export_clustering)
            
        api.add_engine(view, path="subgraph")
        
        @api.route("/ajax_complete")
        def ajax_complete():
            print request.args
            terms = [ request.args.get(e,"") for e in ('lang', 'pos', 'form') ]
            term = ".".join( t for t in terms if t != "" )
            return complete( term )
            
        @api.route("/complete/<string:text>" )
        def complete( text ):
            response = { 'length':0 }
            text = text or ""
            while len(text) and response['length'] == 0 :
                response = tmuse.complete(esindex, text)
                text = text[:-1]
            return jsonify( response )

        @api.route("/_extract/<string:graph>/<string:text>")
        def _extract(graph, text):

            query = Query(graph=graph, form=text)     
            es_res = tmuse.extract(esindex, query)
            return jsonify({ 'res': es_res})
            
        @api.route("/_prox/<string:graph>/<string:text>" )
        def _prox(graph, text):
            
            query = Query(graph=graph, form=text)     

            pz, proxs = tmuse.extract(esindex, query, 10)
            proxs = dict(proxs)
            ids = proxs.keys()
            # request es with ids
            es_res = tmuse.search_docs(esindex, graph, ids)
            return jsonify({ 'ids': ids, 'res': es_res})
            
        return api


def engine(index):
    """ Return a default engine over a lexical graph
    """
    # setup
    from reliure.engine import Engine

    engine = Engine()
    engine.requires("graph", "clustering", "labelling", "layout")
    engine.graph.setup(in_name="query", out_name="graph")
    engine.clustering.setup(in_name="graph", out_name="clusters")
    engine.labelling.setup(in_name="clusters", out_name="clusters", hidden=True)
    engine.layout.setup(in_name="graph", out_name="layout")

    ## Search
    def tmuse_subgraph( query, length=50):        
        return tmuse.subgraph(index, query, length=length)
        
    from cello.graphs.transform import VtxAttr

    graph_search = Optionable("GraphSearch")
    graph_search._func = Composable(tmuse_subgraph)
    graph_search.add_option("length", Numeric( vtype=int, default=50))

    graph_search |= VtxAttr(color=[(45, 200, 34), ])
    graph_search |= VtxAttr(type=1)

    engine.graph.set(graph_search)

    ## Clustering
    from cello.graphs.transform import EdgeAttr
    from cello.clustering.common import Infomap, Walktrap
    #RMQ infomap veux un pds, donc on en ajoute un bidon
    walktrap = EdgeAttr(weight=1.) |Walktrap()
    infomap = EdgeAttr(weight=1.) | Infomap()
    engine.clustering.set(infomap, walktrap)

    ## Labelling
    
    from cello.clustering.labelling.model import Label
    from cello.clustering.labelling.basic import VertexAsLabel, TypeFalseLabel, normalize_score_max
        
    def _labelling(graph, cluster, vtx):
        score = TypeFalseLabel.scoring_prop_ofclust(graph, cluster, vtx)
        return  Label(vtx["form"], score=score, role="default")
    
    labelling = VertexAsLabel( _labelling ) | normalize_score_max
    engine.labelling.set(labelling)

    ## Layout
    from cello.layout.simple import KamadaKawaiLayout
    from cello.layout.proxlayout import ProxLayoutRandomProj
    from cello.layout.proxlayout import ProxLayoutPCA
    from cello.layout.transform import Shaker
    
    engine.layout.set(
        ProxLayoutPCA(dim=3, name="ProxPca3d") | Shaker(), 
        ProxLayoutPCA(dim=2, name="ProxPca2d") | Shaker(), 
        KamadaKawaiLayout(dim=3, name="KamadaKawai3D"),
        KamadaKawaiLayout(dim=2, name="KamadaKawai2D")
    )
    return engine
        