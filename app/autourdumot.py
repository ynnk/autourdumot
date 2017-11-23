#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
import logging

from flask import Flask, abort, make_response
from flask import request, render_template, url_for, abort, jsonify
from flask_analytics import Analytics

from reliure.utils.log import get_basic_logger
from reliure.web import RemoteApi, app_routes

from tmuseapi import TmuseApi, proxlist, QueryUnit
import wiktionary as wk


# Build the app & 
app = Flask(__name__)
app.debug = os.environ.get('APP_DEBUG', None) == "true"
logger = get_basic_logger(logging.DEBUG)

# ajout la config pour le tracker Piwik
if not app.debug:
    Analytics(app)
    app.config['ANALYTICS']['PIWIK']['BASE_URL'] = 'stats.kodexlab.com'
    app.config['ANALYTICS']['PIWIK']['SITE_ID'] = '8'

import requests_cache
cache_file = os.path.dirname(os.path.realpath(__file__))
cache_file = os.path.join(cache_file, '../cache', 'demo_cache.sqlite')
requests_cache.install_cache(cache_file)

# remote api
#tmuseApi = RemoteApi("http://carton.kodexlab.com/tmuse_alpha/tmuse_v1")
#tmuseApi = RemoteApi("http://localhost:5123/tmuse_v1", url_prefix="")

# locale api
ES_HOST = os.environ.get('ES_HOST', "localhost:9200")
ES_INDEX = os.environ.get('ES_INDEX', "autourdumot")
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE', "graph")


from cello.providers.es import EsIndex
esindex = EsIndex(ES_INDEX, doc_type=ES_DOC_TYPE , host=ES_HOST)

tmuseApi = TmuseApi("tmuse_v1", ES_HOST, ES_INDEX, ES_DOC_TYPE)

# Configure the app
app.register_blueprint(tmuseApi)

app.add_url_rule('/_routes', 'routes', lambda : app_routes(app) ,  methods=["GET"])


# index page
@app.route("/")
@app.route("/<string:query>")
@app.route("/<string:query>/<int:count>")
def index(query=None, count = 50):

    return render_template(
         "index_nav.html",
         debug=app.debug,
         count=count,
         root_url=url_for("index"),
         complete_url=url_for("%s.complete" % tmuseApi.name),
         engine_url=url_for("%s.subgraph" % tmuseApi.name),
         random_url=url_for("%s.random_node" % tmuseApi.name),
         def_url=url_for("wkdef", domain="", query="")[:-1] # rm trailing /
    )


@app.route("/export/<string:text>")
@app.route("/export/<string:text>/<int:count>")
def dl(text, count=200, ):
    return liste(text, count, True)

@app.route("/liste/<string:text>")
@app.route("/liste/<string:text>/<int:count>")
def l(text, count=200):
    return liste(text, count, False)

def liste(text, count, inline=False):
    tri = request.args.get('tri', 'score') # score/form
    count = int(request.args.get('count', count))
    
    q = text.split(".") + ['']
    lang, pos, form , ext = q[:4]
    if ext not in ('', 'txt', 'csv', 'tsv') : return abort(404)

    query = QueryUnit(lang=lang, pos=pos, form=form)
    l = proxlist(esindex, query, count)
    l.sort( key=lambda e : e[tri], reverse= tri == 'score' )
    for i,e in enumerate(l) : e['rank']=i+1
    

    if ext == "":
        ROWS = 30
        COLS = 3
        for i,e in enumerate(l) : e['rank']=i+1
        l = [ l[ROWS*i:ROWS*(i+1)]  for i in range( int(count/ROWS)+1 ) ]
        l = [ l[COLS*i:COLS*(i+1)]  for i in range( int(len(l)/COLS)+1 )]
        return render_template( "liste.html", query=text, data=l, tri=tri, count=count)
    else :
        separators = {'txt':" ", 'csv': "," , 'tsv' : '\t'}
        sep = separators[ext]
        
        txt = "\n".join([ "%s%s%s%s%s" % (e['rank'],sep, e['form'],sep, e['score']) for e in l ])
        response = make_response(txt)
        if inline : 
            response.headers['Content-Type'] = 'application/%s' % "text"
            response.headers['Content-Disposition'] = 'inline; filename=%s' % (text)

        return response

    
    

@app.route("/def/<string:domain>/<string:query>")
def wkdef(domain, query):
    """ get and parse definition from wiktionary
        @returns html code of the definition
    """
    pos_headers = { 'A':'Adjectif', 'N':'Nom_commun', 'V':'Verbe', 'E':'Adverbe'}

    data = {}
    try :
        pos = [ request.args.get('pos', None) ]
        allowed = [ pos_headers.get(p, None) for p in pos ]
        allowed = tuple( x for x in allowed if x is not None )
        data = wk.get_wk_definition(domain, query.encode('utf8'), allowed=allowed)
    except Exception as err :
        resp = "<table><tr><td><img src='../static/images/warning.png'/></td><td>" + \
        "can't get definition from <a href='"+query+"' target='_blank'>"+query+"</a>" + \
        "</td></tr></table>"

        data = { 
            'content' : resp,
            'error' : err.message
        }

    return jsonify(data)


def main():
    ## run the app
    from flask.ext.runner import Runner
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())


