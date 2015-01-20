#!/usr/bin/env python
#-*- coding:utf-8 -*-

import igraph 

from reliure import Optionable
from reliure.types import GenericType
from reliure.types import Text, Numeric, Boolean

from cello.schema import Doc, Schema
from cello.graphs.builder import OptionableGraphBuilder

def QueryUnit(**kwargs):
    default = {
        'lang'  : 'fr',
        'pos'   : 'V',
        'form'  : None
    }
    default.update(kwargs)
    default['graph'] = 'jdm.%s.flat' % default['pos']
    return default


class ComplexQuery(GenericType):
    """ Tmuse query type, basicly a list of :class:`QueryUnit`
    
    >>> qtype = ComplexQuery()
    >>> qtype.parse("fr.V.manger")
    [{'lang': 'fr', 'form': 'manger', 'graph': 'jdm.V.flat', 'pos': 'V'}]
    >>> qtype.parse("fr.A.rouge fr.A.bleu")
    [{'lang': 'fr', 'form': 'rouge', 'graph': 'jdm.A.flat', 'pos': 'A'}, {'lang': 'fr', 'form': 'bleu', 'graph': 'jdm.A.flat', 'pos': 'A'}]
    >>> qtype.parse([{'lang': 'fr', 'form': 'manger', 'pos': 'V'}])
    [{'lang': 'fr', 'form': 'manger', 'graph': 'jdm.V.flat', 'pos': 'V'}]
    >>> qtype.parse([{'form': 'manger'}])
    [{'lang': 'fr', 'graph': 'jdm.V.flat', 'pos': 'V', 'form': 'manger'}]
    """
    def parse(self, value):
        query = []
        if isinstance(value, basestring):
            for ele in value.split():
                ele = ele.strip().split(".")
                qunit = {}
                qunit["form"] = ele[-1]
                if len(ele) >= 2:
                    qunit["pos"] = ele[-2]
                    if len(ele) >= 3:
                        qunit["lang"] = ele[-3]
                query.append(QueryUnit(**qunit))
        else:
            query = [
                QueryUnit(**{k:v for k,v in val.iteritems() if v is not None})
                for val in value
            ]
        return query

    @staticmethod
    def serialize(complexquery):
        uri = ",".join([  '.'.join( ( q['lang'], q['pos'], q['form'] ) ) for q in complexquery ])
        return {
            'units': complexquery,
            'uri': uri
       }


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
        p0, vect = extract(index, q, 500)
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

    print 'graphname', query[0]['graph']
    print 'pzeros', [ q['form'] for q in query ]
    print 'ids', ids
    print 'pzeros', pzeros
    print 'docs', len(docs)
    print 'g', graph.summary()
    
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
        
    print body
    res = index.search(body=body, size=1)
        
    if 'hits' in res and 'hits' in res['hits']:
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


class TmuseEsComplete(Optionable):
    """ auto complete helper to find matching candidates 
    
    Usage exemple:
    >>> from cello.providers import es
    >>> index = es.EsIndex("docs", host="localhost:9200")
    >>> completion = TmuseEsComplete(index)
    
    Options:
    >>> completion.print_options()
    size (Numeric, default=20): Max number of propositions
    """
    def __init__(self, index, field='form_suggest'):
        """

        :param index: <EsIndex> to search candidates
        :param field: the field to use for autocompletion
        """
        super(TmuseEsComplete, self).__init__()
        self.es_idx = index
        self.field = field
        self.add_option("size", Numeric(
            vtype=int, min=0, max=300, default=20,
            help="Max number of propositions"
        ))

    @Optionable.check
    def __call__(self, lang, pos, form, size=None):
        text = form
        prefix = []
        if lang != u"*":
            prefix.append(lang)
        if pos != u"*":
            prefix.append(pos)
        if len(prefix):
            prefix = ".".join(prefix)
        else:
            prefix = "*"

        self._logger.debug("Ask completion, prefix=%s text=%s" % (prefix, text))
        # preparing response data
        response = {
            'prefix': prefix,
            'text': text,
            'length': 0,
            'complete': []
        }

        key = "word_completion"
        body = {
            key: {
                "text": text,
                "completion": {
                    "field": self.field,
                    "size": size,
                    "context": {
                        "prefix": prefix
                    }
                }
            }
        }
        res = self.es_idx.suggest(body=body)
        # process results (if any)
        if key in res and res[key][0].get('length', 0):
            complete = []
            options = res[key][0]['options']
            for opt in options:
                complete.append({
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

