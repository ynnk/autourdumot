#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
GLÀFF is based on Wiktionnaire, and constitutes a derivative work from this resource.
It is available under the same licence: 
Creative Commons By-SA 3.0 (Attribution - ShareAlike 3.0 Unported). 
Please read carefully this licence before using GLÀFF.

Concepteurs
Franck Sajous, Nabil Hathout et Basilio Calderone

Responsable ressource
Franck Sajous
Contact : sajous@univ-tlse2.fr 

homepage : http://redac.univ-tlse2.fr/lexiques/glaff.html
dl : http://redac.univ-tlse2.fr/lexiques/glaff/GLAFF-1.2.1.tar.bz2  
"""

import sys
import argparse


LICENCE = "WTFL" or "Creative Commons By-SA 3.0"


def parse(path):
    glaff = {}
    try:
        with open(path, 'r') as fin:
            for line in fin:
                spl = line.split('|')
                form , pos, lemma = spl[:3]
                pos = pos[0]

                key = '%s.%s' % (pos, lemma)
                entry = glaff.get(key,[])
                entry.append(form)
                glaff[key] = entry
    except:
        print("Error while parsing Glaff data \nAre you sure glaff is there ?")
    return glaff


def main():
    """ Function doc
    :param : 
    """    
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument("--option", action='store_true',help="")
    args = parser.parse_args()

    path = "GLAFF-1.2.1/glaff-1.2.1.txt"
    glaff = parse(path)
    print(len(glaff))

if __name__ == '__main__':
    sys.exit(main())
    
