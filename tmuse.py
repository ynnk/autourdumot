#!/usr/bin/env python
#-*- coding:utf-8 -*-
import random
import igraph 

from reliure import Optionable
from reliure.exceptions import ReliureValueError, ReliurePlayError

from reliure.types import GenericType
from reliure.types import Text, Numeric, Boolean

from cello.schema import Doc, Schema
from cello.graphs.builder import OptionableGraphBuilder



class WrongQueryError(ReliurePlayError):
    """ when qury unit is malformed """
    
class NoResultError(ReliurePlayError):
    """ when query returns no result """

class TmuseEsGraphBuilder(OptionableGraphBuilder):
    """ Build a graph from a tmuse Unipartite link graph """
    def __init__(self, directed=False, reflexive=True, label_attr='form', vtx_attr='docnum', links_attr="out_links"):
        # Optionable init 
        OptionableGraphBuilder.__init__(self, "GraphBuilder", directed=False)
        self.reflexive = reflexive
        
        self.add_option("label_attr", Text( vtype=str, default=label_attr))
        self.add_option("vtx_attr", Text( vtype=str, default=vtx_attr))
        self.add_option("links_attr", Text( vtype=str, default=links_attr))
        
         # Graph builder init

        vattrs = ("_doc", "rank", "pzero", "docnum", "graph","lang", 
                  "pos", "form", "score","neighbors")
        map( self.declare_vattr, vattrs )

        eattrs = ("weight",)
        map( self.declare_eattr, eattrs )

    @OptionableGraphBuilder.check
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
            self.set_vattr(doc_gid, "pzero", kdoc['pzero'])
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


def random_node(index, graph):
    body = {
              "_source": ["prox", "neighborhood"],
              "query": {
                "function_score": {
                  "filter": {
                    "term": { "graph": graph }
                  },
                  "functions": [
                    {
                      "random_score": {}
                    }
                  ],
                  "score_mode": "sum"
                }
              }
            }

    docs = []
    res = index.search(body=body, size=1)
    if 'hits' in res and 'hits' in res['hits']:
        hits = res['hits']['hits']
        candidates = [ i for i,_ in hits[0]['_source']['prox'][:50]]
        candidates = hits[0]['_source']['neighborhood']
        ids  = [  i for i in candidates ]
        vid = random.sample(ids,1)
        docs = [ d['_source'] for d in search_docs(index, graph, vid)['hits']['hits'] ]

    return docs
    
    

def subgraph(index, query, length=50):
    """
    no test on query [{}, {}, ...]
    :param index: <EsINndex>  forms 
    :param query: [<str>] or <str>  forms 
    :param length: <int>  resultset size 
    """

    
    # get vertex ids
    proxs = {}
    pzeros = []
    for q in query:
        if q['form'] in ('', None):
            raise WrongQueryError("Un mot doit être sasie pour effectuer une recherche.")  
        
        result = extract(index, q, 500)
        if not len(result): 
            raise WrongQueryError(u"Aucun résultat pour le mot '%s'." % q['form'])  


        p0, vect = result
        for k,v in vect:
            proxs[k] = proxs.get(k,0.) + v;
        pzeros.append(p0)
        
    proxs = proxs.items()
    proxs.sort(key=lambda x : x[1], reverse=True)
    proxs = dict(proxs[:length])
    
    ids = proxs.keys()
    # request es with ids
    res = search_docs(index, query[0]['graph'], ids)
    # convert res to docs
    docs = to_docs(res, pzeros)
    
    docs.sort(key=lambda x : proxs[x.docnum], reverse=True)
    
    
    # build graph from docs
    graph = to_graph(docs)
    
    return graph


def extract(index, q,  length=50):
    body = {
            "_source": ['graph', 'form','gid', 'prox', 'neighbors'],
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
        
    res = index.search(body=body, size=1)
        
    if 'hits' in res and 'hits' in res['hits']:
        if len(res['hits']['hits']) :
            doc = res['hits']['hits'][0]['_source']
            proxs  = [  p for p in doc['prox'] ]
            return (doc['gid'], proxs[:length])

    return []


def to_graph(docs, pzeros=[]):
    
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
    pzero=Boolean(),
    form=Text(vtype=str),
    neighbors=Numeric(),
    out_links=Numeric(multi=True, uniq=True),
    # computed fields
    rank=Numeric(),
    score=Numeric(vtype=float, default=0.)
)

def to_docs(es_res, pzeros):
    _pzeros = set(pzeros) or set([]) 
    docs = []
    if 'hits' in es_res and 'hits' in es_res['hits']:
        for doc in es_res['hits']['hits']:
            data = {}
            data["docnum"] = doc["_source"]["gid"]
            data["pzero"] = doc["_source"]["gid"] in _pzeros
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


def complete(index, prefix, text, field='form_suggest', size=100):
    """ auto complete helper to find matching candidates 
    :param index: <EsIndex> to search candidates
     
    """
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
        max_score = 0
        for opt in options:
            complete.append( {
                "graph": opt['payload']['graph'],
                "lang": opt['payload']['lang'],
                "pos": opt['payload']['pos'],
                "form": opt['payload']['form'],
                "score": opt['score'],
                "output": opt['text']
            })
            max_score = max(max_score, opt['score'])

        for v in complete:
            score = v['score']/max_score
            if text == v['form']:
                score +=1
            v['score'] = score

        complete.sort(key=lambda x : x['score'], reverse=True)
            
        response['length'] = len(complete)
        response['complete'] = complete
        response['size'] = size
    
    return response


