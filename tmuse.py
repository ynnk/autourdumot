#!/usr/bin/env python
#-*- coding:utf-8 -*-

import igraph 

from reliure.types import Text, Numeric, Boolean
from reliure.pipeline import Optionable, Composable

from cello.schema import Doc, Schema
from cello.graphs.builder import OptionableGraphBuilder


class TmuseEsGraphBuilder(OptionableGraphBuilder):
    """ Unipartite link graph """
    def __init__(self, directed=False, reflexive=True, label_attr='form', vtx_attr='docnum', links_attr="out_links"):
        # Optionable init 
        OptionableGraphBuilder.__init__(self, "GraphBuilder", directed=False)
        self.reflexive = reflexive
        
        self.add_option("label_attr", Text( vtype=str, default=label_attr))
        self.add_option("vtx_attr", Text( vtype=str, default=vtx_attr))
        self.add_option("links_attr", Text( vtype=str, default=links_attr))
        
         # Graph builder init

        vattrs = ("_doc", "rank", "docnum", "graph","lang", 
                  "pos", "form", "score","neighbors")
        map( self.declare_vattr, vattrs )

        eattrs = ("weight",)
        map( self.declare_eattr, eattrs )
    
    @Optionable.check
    def __call__(self, docs, vtx_attr='form', links_attr='out_links', label_attr='form'):

        encode = lambda x: x.encode('utf8') if  type(x) == unicode else str(x)
        kdocs = list(docs)
        docset = set([doc[vtx_attr] for doc in kdocs])
                
        self.reset()

        for rank, kdoc in enumerate(kdocs):
            # ajout doc
            did = kdoc[vtx_attr]
            doc_gid = self.add_get_vertex(did)
            self.set_vattr(doc_gid, "_doc", kdoc)
            self.set_vattr(doc_gid, "rank", rank+1)
            self.set_vattr(doc_gid, "docnum", kdoc['docnum'])
            self.set_vattr(doc_gid, "neighbors", kdoc['neighbors'])
            self.set_vattr(doc_gid, "graph", encode(kdoc['graph']))
            self.set_vattr(doc_gid, "lang", encode(kdoc['lang']))
            self.set_vattr(doc_gid, "pos", encode(kdoc['pos']))
            self.set_vattr(doc_gid, "form", encode(kdoc['form']))
            self.set_vattr(doc_gid, "score", kdoc['score'])
            
        for kdoc in kdocs:
            did = kdoc[vtx_attr]
            doc_gid = self.add_get_vertex(did)
            
            # ajout liens
            for link in ( target for target in kdoc[links_attr] if target in docset):
                link_id = self.add_get_vertex(link)
                eid = self.add_get_edge(doc_gid, link_id)
                self.set_eattr(eid, "weight", 1)

        graph = self.create_graph()
        if 'id' in graph.vs.attributes():
            del graph.vs['id']
            
        return graph


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
        return subgraph(index, query, length=length)
        
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


def subgraph(index, query, length=50):
    """
    no test on query [{}, {}, ...]
    :param index: <EsINndex>  forms 
    :param query: [<str>] or <str>  forms 
    :param length: <int>  resultset size 
    """

    
    # get vertex ids
    proxs = {}
    for q in query:
        vect = dict(extract(index, q, 500))
        for k,v in vect.iteritems():
            proxs[k] = proxs.get(k,0) + v;
    proxs = proxs.items()
    proxs.sort(key=lambda x : x[1], reverse=True)
    proxs = dict(proxs[:length])
    
    ids = proxs.keys()
    # request es with ids
    res = search_docs(index, query[0]['graph'], ids)
    # convert res to docs
    docs = to_docs(res)
    
    docs.sort(key=lambda x : proxs[x.docnum], reverse=True)
    
    
    # build graph from docs
    graph = to_graph(docs)

    print 'graphname', query[0]['graph']
    print 'pzeros', [ q['form'] for q in query ]
    print 'ids', ids
    print 'docs', len(docs)
    print 'g', graph.summary()
    

    return graph
    
        
def extract(index, q,  length=50):
    body = {
            "_source": ['graph', 'form','prox', 'neighbors'],
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            { "term": {"graph": q['graph']} },
                            { "term": {"lang" : q['lang']} },
                            { "term": {"pos"  : q['pos']} },
                            { "term": {"form" : q['form'].encode('utf8')} },
                        ]
                   }
                }  
            }
        }
        
    print body
    res = index.search(body=body, size=1)
        
    if 'hits' in res and 'hits' in res['hits']:
        docs = [ doc['_source'] for doc in res['hits']['hits']]
        proxs  = [  p for doc in docs for p in doc['prox'] ]
    
    return proxs[:length]

def to_graph(docs):
    
    build_graph = TmuseEsGraphBuilder()
    graph = build_graph(docs)
        
    return graph

    

def search_docs(index, graph, ids):
    
    docs = []
    q = { 
        "_source":['graph', 'lang', 'pos', 'form', 'gid','neighbors', 'neighborhood'],
        "query": {
            "filtered" : {
                "query": { 
                    "terms": { 
                        'gid': ids,
                    },
                },
                "filter" : {
                    "bool" : {
                        "must" : {
                            "term" : {
                                "graph" : graph,
                            }
                        }
                    }
                }
            }
        }
    } # /q
    
    res = index.search(body=q, size=len(ids))
    return res

TmuseDocSchema = Schema(
    docnum=Numeric(),
    # stored fields
    graph=Text(vtype=str),
    lang=Text(vtype=str),
    pos=Text(vtype=str),
    form=Text(vtype=str),
    neighbors=Numeric(),
    out_links=Numeric(multi=True, uniq=True),
    # computed fields
    rank=Numeric(),
    score=Numeric(vtype=float, default=0.)
)    

def to_docs(es_res):
    docs = []
    if 'hits' in es_res and 'hits' in es_res['hits']:
        for doc in es_res['hits']['hits']:
            data = {}
            data["docnum"] = doc["_source"]["gid"]
            data["graph"] = doc["_source"]["graph"].encode('utf8')
            data["lang"] = doc["_source"]["lang"].encode('utf8')
            data["pos"] = doc["_source"]["pos"].encode('utf8')
            data["form"] = doc["_source"]["form"].encode('utf8')
            data["out_links"] = doc["_source"]["neighborhood"]
            data["neighbors"] = doc["_source"]["neighbors"]
            data["score"] = doc.get('_score', -1)
            
            docs.append( Doc(TmuseDocSchema, **data) )
 
    print [ doc['_source']['form'] for doc in es_res['hits']['hits']]
    
    return docs




    

def complete(index, text, field='form_suggest', size=100):
    """ auto complete helper to find matching candidates 
    :param index: <EsIndex> to search candidates
     
    """
    prefix = ["*"]

    splitted = text.split(".")
    if len(splitted) > 1 :
        text = splitted[-1]
        prefix = splitted[:-1]
        if len(prefix) > 1 :
            prefix = ".".join(prefix) 
    
    response = { 'prefix': prefix, 'text':text, 'length': 0, 'complete': [] }
    
    key = "word_completion"
    body = {
        key: {
            "text": text,
            "completion": {
                "field": field,
                "size": size,
                "context": {
                    "prefix": prefix
                }
            }
        }
    }
    res = index.suggest(body=body)
    #return res
    if key in res and res[key][0].get('length', 0) :
        complete = []
        
        options = res[key][0]['options']
        for opt in options:
            complete.append( {
                "graph": opt['payload']['graph'],
                "lang": opt['payload']['lang'],
                "pos": opt['payload']['pos'],
                "form": opt['payload']['form'],
                "score": opt['score'],
                "output": opt['text']
            })
            
        response['length'] = len(complete)
        response['complete'] = complete
        response['size'] = size
    
    return response
