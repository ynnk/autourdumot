#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import argparse
import igraph
from itertools import islice
import yaml 

from cello.providers.es import EsIndex, ESPhraseSuggest
import cello.graphs.prox as prox

import glaff


dirpath = "%s/Graphs" % os.environ['PTDPATH']

dicosyn =  [ 
            {   'name': 'dicosyn.V',
                'path':  "%s/dicosyn/dicosyn/V.dicosyn.pickle" % dirpath,
                'pos' : 'V',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'dicosyn.N',
                'path':  "%s/dicosyn/dicosyn/N.dicosyn.pickle" % dirpath,
                'pos' : 'N',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'dicosyn.A',
                'path':  "%s/dicosyn/dicosyn/A.dicosyn.pickle" % dirpath,
                'pos' : 'A',
                'lang': 'fr',
                'completion' : glaff_completion
            },
        ]
jdm = [
            {   'name': 'jdm.A',
                'path':  "%s/jdm/fr.A.JDM-01282014-v1-e5-s_avg.pickle" % dirpath,
                'pos' : 'A',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'jdm.N',
                'path':  "%s/jdm/fr.N.JDM-01282014-v1-e5-s_avg.pickle" % dirpath,
                'pos' : 'N',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'jdm.V',
                'path':  "%s/jdm/fr.V.JDM-01282014-v1-e5-s_avg.pickle" % dirpath,
                'pos' : 'V',
                'lang': 'fr',
                'completion' : glaff_completion
            },
        ]

jdm_flat = [
            {   'name': 'jdm.A.flat',
                'path':  "%s/jdm/fr.A.JDM-12312014-v1_666_777-e5-s_avg-flat.pickle" % dirpath,
                'pos' : 'A',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'jdm.N.flat',
                'path':  "%s/jdm/fr.N.JDM-12312014-v1_666_777-e5-s_avg-flat.pickle" % dirpath,
                'pos' : 'N',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'jdm.V.flat',
                'path':  "%s/jdm/fr.V.JDM-12312014-v1_666_777-e5-s_avg-flat.pickle" % dirpath,
                'pos' : 'V',
                'lang': 'fr',
                'completion' : glaff_completion
            },
            {   'name': 'jdm.E.flat', # adverbes
                'path':  "%s/jdm/fr.E.JDM-12312014-v1_666_777-e5-s_avg-flat.pickle" % dirpath,
                'pos' : 'E',
                'lang': 'fr',
                'completion' : glaff_completion
            },
        ]

def index(es_index, cut_local = 500, cut_global = -1, **kwargs):
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

    graph = igraph.read( path )
    
    # { idx : (rank, prox) }    
    pg = prox.prox_markov_dict(graph, [], 4, add_loops=True)
    pg = prox.sortcut(pg, cut_global)
    pg = { e[0]: ( rank+1, e[1] ) for rank, e in enumerate(pg) }
    
    def _prox(pzero):
        pl = prox.prox_markov_dict(graph, pzero, 3, add_loops=True)
        cut = prox.sortcut(pl, 500)
        return cut
        
    def iter_vertices():
        for i, k in enumerate(pg):
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
            
            line = "%s %s/%s %s %s" % (name, i, graph.vcount(), len(neighborhood),  label)
            line = line.encode('utf8')
            print line

            yield body
    
    es_index.add_documents(iter_vertices())

def main():    
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument("--host", action='store',default='localhost', help="")
    parser.add_argument("-i", dest='index', action='store_true',default=False, help="index")
    parser.add_argument("--drop", dest='drop', action='store_true',default=False, help="drop index before indexing")
    parser.add_argument("-s", dest='suggest', action='store',nargs=2, help="suggest field text")
    
    parser.add_argument("--noprompt", dest='noprompt', action='store_false',default=True, help="No user prompt ")
    
    parser.add_argument("name", action='store',help="index name")

    args = parser.parse_args()
    
    schema_path = "./schema.yml"

    glaff_data = glaff.parse("GLAFF-1.2.1/glaff-1.2.1.txt")
    
    if args.noprompt and not len(glaff_data):
        read = raw_input('No glaff data \n <Enter> to continue <ctrl C> to stop')
    
    def glaff_completion(lang, pos, lemma):
        candidates = set([lemma])
        candidates.update( set( glaff_data.get( "%s.%s" % (pos, lemma) , [])) )
        return list(candidates)
    
    if args.index:
        schema = yaml.load(open(schema_path))
        es_index = EsIndex(args.name, host=args.host, doc_type='graph', schema=schema['mappings']['graph'])

        if args.drop and es_index.exists():
            es_index.delete(full=True)
        if not es_index.exists():
            es_index.create()

        #graphs = dicosyn + jdm + jdm_flat
        graphs = jdm_flat

        for conf in graphs:
            index(es_index, **conf) 
    
if __name__ == '__main__':
    sys.exit(main())
