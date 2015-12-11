#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import argparse
import igraph
import yaml 
import unicodedata
from itertools import islice

from cello.providers.es import EsIndex, ESPhraseSuggest
import cello.graphs.prox as prox

import glaff


def index(es_index, cut_local=500, cut_global=-1, lcc=False, start=0, offset=0, **kwargs):
    """
    :param cut_global: <int> global vector cut -1 to keep all
    :param cut_local: <int> local vector cut -1 to keep all
    """
    path = kwargs['path']
    name = kwargs['name']
    lang = kwargs['lang']
    pos  = kwargs['pos']
    # completion from other resource goes to inputs
    completion = kwargs['completion']
    if completion is None:
        completion = lambda lang, pos, text: text

    graph = igraph.read(path)

    if lcc:
        graph = graph.clusters().giant()

    print(graph.summary())

    # { idx : (rank, prox) }    
    pg = prox.prox_markov_dict(graph, [], 4, add_loops=True)
    pg = prox.sortcut(pg, cut_global)
    pg = { e[0]: (rank+1, e[1]) for rank, e in enumerate(pg) }

    def _prox(pzero):
        pl = prox.prox_markov_dict(graph, pzero, 3, add_loops=True)
        cut = prox.sortcut(pl, 500)
        return cut

    def iter_vertices():
        count = 0
        for i, k in enumerate(pg):
            if i < start:
                continue
            if offset and count >= offset:
                break

            count +=1
            vtx = graph.vs[k]
            label = vtx['label']
            neighborhood = graph.neighborhood(vtx)
            body =  {
                'gid' : k,
                'graph': name,
                'lang': lang,
                'pos' : pos,
                'form': vtx['label'],
                'neighbors': len(neighborhood),
                'neighborhood': neighborhood,
                'prox': _prox([k]),
                'rank': pg[k][0],
                'form_suggest': { 
                    "input": completion(lang, pos, label),
                    "output": "/".join( (name, lang, pos, label)),
                    "context": {
                        'prefix': ["*", lang, pos, '%s.%s'%(lang, pos) ]
                    },
                    "weight" : len(neighborhood),
                    "payload": {
                        'graph': name,
                        'lang': lang,
                        'pos' : pos,
                        'form' : label
                    }
                }
            }
            
            line = "%s %s %s/%s %s %s" % (name, k, i, graph.vcount(), len(neighborhood),  label)
            line = line.encode('utf8')
            print(line)

            yield body

    es_index.add_documents(iter_vertices())


def main(): 
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument("--host", action='store',default='localhost', help="ElasticSearch hostname")
    parser.add_argument("--idx", action='store', help="ES index name")

    parser.add_argument("-d", "--drop", dest='drop', action='store_true', default=False, help="Drop index before indexing")

    #parser.add_argument("--lcc", dest='lcc', action='store_true', default=False, help="Computes only lcc of the loaded graph")

    parser.add_argument("--start", dest='start', action='store', type=int, help="Indexing start from", default=0)
    parser.add_argument("--offset", dest='offset', action='store', type=int, help="offset", default=0)

    parser.add_argument("--gname", action='store', help="Graph name")
    parser.add_argument("--gpath", action='store', help="Graph path")
    parser.add_argument("--gpos", action='store', help="POS of graph vertices")
    parser.add_argument("--glang", action='store', help="Language of graph vertices")

    args = parser.parse_args()

    schema_path = "./schema.yml"

    ## Glaff for autocompletion
    glaff_data = glaff.parse("GLAFF-1.2.1/glaff-1.2.1.txt")

    def glaff_completion(lang, pos, lemma):
        candidates = set([lemma])
        candidates.update( set( glaff_data.get( "%s.%s" % (pos, lemma) , [])) )
        return list(candidates)

    def no_accent(lang, pos, lemma):
        return [''.join(c for c in unicodedata.normalize('NFD', lemma) if unicodedata.category(c) != 'Mn')]

    def completion(lang, pos, lemma):
        methods  = (glaff_completion, no_accent)
        complete = []
        for mth in methods:
            complete.extend(mth(lang, pos, lemma))
        return list(set(complete))

    graph_conf = {
        'name': args.gname,
        'path': args.gpath,
        'pos' : args.gpos,
        'lang': args.glang,
        'completion': completion,
    }

    schema = yaml.load(open(schema_path))
    es_index = EsIndex(args.idx, host=args.host, doc_type='graph', schema=schema['mappings']['graph'])

    if args.drop and es_index.exists():
        es_index.delete(full=True)

    if not es_index.exists():
        es_index.create()

    if graph_conf['name'] is not None:
        print("indexing:%s" % (graph_conf['name']))
        index(es_index, start=int(args.start), offset=int(args.offset), **graph_conf)

if __name__ == '__main__':
    sys.exit(main())

