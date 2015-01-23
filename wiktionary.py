#!/usr/bin/env python
#-*- coding:utf-8 -*-
import re
import requests
import lxml
from pyquery import PyQuery as pq
from  urllib import quote
    

def get_arg(path):
    args = [ i for i in path.split('/') if not i == ""]
    return args[-1]
    
def _pyquery_requests_opener(url):
    # TODO : set headers to trick user agent
    xml = requests.get(url).content
    xml = xml.replace(' xmlns=', ' ns=') # hack  namespace lxml bug
    return xml.decode('utf8')



def get_wk_definition(domain, query, allowed=None):
    """
    :param allowed: None or [] returns all headlines
        compare keys on the same length
        ex: allowed=("boo",) would allow headlines "boo", "boolean"
    """        
    assert allowed is None or type(allowed) in (list, tuple, set), "Wrong type for 'allowed"
    base_url = "http://%s.wiktionary.org" % domain
    url = "%s/wiki/%s" % (base_url, quote(query))
    
    p = pq(url=url, opener=_pyquery_requests_opener)
    content = p('#bodyContent').html()

    # clean ids
    ids_to_replace = {
        ".C3.A9" : u"e",
        ".C3.89" : u"E",
        ".C3.A0" : u"à"
    }

    for k,v in ids_to_replace.iteritems():
        content = content.replace(k,v)

    # removes useless data
    useless = ('#contentSub', '#siteSub' ,'#jump-to-nav', '#toc', '#catlinks', '.printfooter', '.visualClear', '.mw-editsection', '.editsection',# section edit
    'h1', 'h2', #'h3', # titles
    '.flextable', # table singulier / pluriel
    #'#References'
    ) 

    definition = pq(content)
    for i, e in enumerate(useless):
        definition.remove(e) 
    
    # change links to open in new window
    for link in definition.find('a'):
        href = pq(link).attr('href')
        if href[0] != "#" and href[0:4] != "http" : # not an anchor or external link
            pq(link).attr('target' , '_blank')
            pq(link).attr('href', base_url + href)
    
    # fix img src url
    for img in definition.find('img'):
        src = pq(img).attr('src')
        if src[0] == "/" and not src[1] == "/": 
            pq(img).attr('src', domain + src)

    # sections cachees class: wk-hiddable
    # sub def sections
    cachable = ( "#mw-content-text ol li ul", )
    for i, e in enumerate(cachable):
        pq(e,definition).addClass("wk-hiddable")

    # headlines ".mw-headline"
    tag = lambda x : str(x.tag()) if callable(x.tag) else x.tag 

    headlines = map(lambda e :  pq(e).attr('id'), pq(".mw-headline", definition) )
    
    # add  wk-headline class to headlines and all following tag until next <Hx> 
    if allowed is not None and len(allowed):
        for i, e in enumerate(headlines):
            if any( key == e[:len(key)] for key in allowed  ):
                continue

            el = pq("#%s" % e, definition).parent()
            el.addClass('wk-hiddable')
            while True:
                el = el.next()
                # stop if not next or tag is title 'h1..'
                if not len(el): break
                if tag(el[0]).lower().startswith('h'): break
                # skip comments
                if type(el[0]) == lxml.html.HtmlComment : continue
                
            el.addClass('wk-hiddable')
    # data    
    return  { 'domain': domain,
              'url' : url,
              'query' : query,
              'content' : definition.html().encode('utf8'),
            }


