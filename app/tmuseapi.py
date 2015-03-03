#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import request, jsonify

from reliure.types import GenericType, Text, Numeric
from reliure.web import ReliureAPI, EngineView, ComponentView, RemoteApi
from reliure.pipeline import Optionable, Composable

from cello.graphs import export_graph, IN, OUT, ALL
from cello.layout import export_layout
from cello.clustering import export_clustering
from cello.providers.es import EsIndex

import tmuse

ALL_POS = ('A', 'V', 'N', 'E')

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



def TmuseApi(name, host='localhost:9200', index_name='tmuse', doc_type='graph'):
    """ API over tmuse elastic search
    """
    esindex = EsIndex(index_name, doc_type=doc_type , host=host)
    print "# TmuseApi", host, doc_type, index_name 
    assert esindex._es.ping(), "impossible to reach ES server"

    # build the API from this engine
    print "api name", name
    api = ReliureAPI(name)

    # Main api entry point: tmuse engine (subgraph)
    view = EngineView(engine(esindex))
    view.set_input_type(ComplexQuery())
    view.add_output("query", ComplexQuery())
    view.add_output("graph", export_graph)
    view.add_output("layout", export_layout)
    view.add_output("clusters", export_clustering)
    # add a simple play route
    view.play_route("<query>")
    api.register_view(view, url_prefix="subgraph")

    # Add auto completion View
    completion = TmuseEsComplete(index=esindex, size=20)
    # TODO suggestion rerank
    # completion |= rerank
    completion_view = ComponentView(completion)
    completion_view.add_input("lang", Text(default=u"*"))
    completion_view.add_input("pos", Text(default=u"*"))
    completion_view.add_input("form")
    completion_view.add_output("response")
    completion_view.play_route("<lang>.<pos>.<form>")
    api.register_view(completion_view, url_prefix="complete")

    import random

    @api.route("/random")
    @api.route("/random/<string:pos>")
    def random_node(pos=None, retry=5, count=0 ):
        if pos not in ALL_POS :
            pos = random.sample(ALL_POS, 1)[0]
            
        graph = "jdm.%s.flat" % pos
        docs = tmuse.random_node(esindex, graph)

        doc = docs[0] if len(docs) else dict()
            
        return jsonify({ 'pos':pos, 'doc': doc})
        
        
    # Debug views
    @api.route("/_extract/<string:graph>/<string:text>")
    def _extract(graph, text):
        query = QueryUnit(graph=graph, form=text)
        es_res = tmuse.extract(esindex, query)
        return jsonify({ 'res': es_res})
        
    @api.route("/_prox/<string:graph>/<string:text>" )
    def _prox(graph, text):
        query = QueryUnit(graph=graph, form=text)
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

    engine = Engine("graph", "clustering", "labelling", "layout")
    engine.graph.setup(in_name="query", out_name="graph")
    engine.clustering.setup(in_name="graph", out_name="clusters")
    engine.labelling.setup(in_name="clusters", out_name="clusters", hidden=True)
    engine.layout.setup(in_name="graph", out_name="layout")

    ## Search
    def tmuse_subgraph(query, length=50):
        return tmuse.subgraph(index, query, length=length)

    graph_search = Optionable("GraphSearch")
    graph_search._func = Composable(tmuse_subgraph)
    graph_search.add_option("length", Numeric( vtype=int, default=50))

    from cello.graphs.transform import VtxAttr
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
        ProxLayoutPCA(dim=3, name="ProxPca3d") | Shaker(kelastic=.9),
        ProxLayoutPCA(dim=2, name="ProxPca2d") | Shaker(kelastic=1.8),
        KamadaKawaiLayout(dim=3, name="KamadaKawai3D"),
        KamadaKawaiLayout(dim=2, name="KamadaKawai2D")
    )
    return engine

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
    def __init__(self, index, field='form_suggest', size=10):
        """

        :param index: <EsIndex> to search candidates
        :param field: the field to use for autocompletion
        :param size: default value for options 'size'
        """
        super(TmuseEsComplete, self).__init__()
        self.es_idx = index
        self.field = field
        self.add_option("size", Numeric(
            vtype=int, min=0, max=300, default=size,
            help="Max number of propositions"
        ))

    @Optionable.check
    def __call__(self, lang, pos, form, size=None):
        """
        recursive call to tmuse.complete until text match suggestion
        removing last character during each call
        """
        response = {}
        params = dict(field=self.field, size=size)
        
        text = form or ""
        prefix = []
        if lang != u"*":
            prefix.append(lang)
        if pos != u"*":
            prefix.append(pos)
        if len(prefix):
            prefix = ".".join(prefix)
        else:
            prefix = "*"
        
        while len(text) and response.get('length',0) == 0 :
            self._logger.debug("Ask completion, prefix=%s text=%s" % (prefix, text))
            response = tmuse.complete(self.es_idx, prefix, text, **params )
            text = text[:-1]

        return response
