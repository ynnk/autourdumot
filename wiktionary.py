#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys
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
    print "Wiktionary", url
    p = pq(url=url, opener=_pyquery_requests_opener)
    content = p('#bodyContent').html()

    # clean ids
    ids_to_replace = {
        ".C3.A9" : u"e",
        ".C3.89" : u"E",
        ".C3.A0" : u"à",
        ".E2.80.99" : "_"
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


def extract_syn(dump_path):
    
    from xml.sax.handler import ContentHandler
    from xml.sax import make_parser
    from collections import namedtuple

    re_lang = re.compile(r"== {{langue\|(.+)}} ?==")
    #re_pos  = re.compile(r"=== {{S\|([^\|]+)\|+.+}} ?===")
    #re_pos = re.compile(r"=== {{S\|([^\|]+)(?:\|.+)?}} ===")
    re_pos = re.compile(r"=== {{S\|([^\|]+\|?){,5}}} ===")
    re_sect = re.compile(r"==== {{S\|([^\|]+)(?:\|.+)?}} ====")
    re_syns = re.compile(r"\[\[([^\[\]]+)\]\]")
    
    def parseArticle(title, text):

        art = namedtuple("Article", 'lang pos section syns')
        art.lang = None
        art.pos = None
        art.section = None
        art.syns = []

        def _flush():
            if art.lang and art.pos and art.section and len(art.syns):
                syns = ",".join([ s for s in art.syns ])
                line = ";".join( x for x in  [title, art.lang, art.pos, art.section, syns])
                print  line.encode('utf8')
                art.syns = []

        
        for line in text.split('\n'):
            line = line.strip()
                
            if line.startswith("== {{langue|"):
                _flush()
                l = re_lang.findall(line)
                if len(l) :
                    art.lang = l[0]
                
            elif line.startswith("=== {{S|"):
                _flush()
                m = re_pos.findall(line)
                m = re.findall(r'(\w+)', line, re.UNICODE ) 
                if len(m) > 1:
                    art.pos = m[1]
                
            elif line.startswith("==== {{S|"):
                _flush()
            
                m = [ x for x  in re_sect.findall(line) if len(x) ]
                #print ";".join( repr(x) for x in  [art.lang, title, line, ", ".join( [ repr(_) for _ in m ])]).encode('utf8')
                if len(m): 
                    art.section = m[0]
                    
            else :
                if art.lang == "fr" and art.section == "synonymes" and art.pos in ('adjectif', 'nom', 'verbe'):
                    if line[:1] == "*":
                        art.syns.extend( re_syns.findall(line) )

    
    class myHandler(ContentHandler):
        title = None
        text = None
        chflag = False

        def startElement(self, name, attrs):
            self.chflag = False 

            if name == "page":
                self.title = None
                self.text = None
            elif name == "title":
                self.text = ""
                self.chflag = True
            elif name == "text":
                self.text = ""
                self.chflag = True 

        def endElement(self, name):
            if name == "title":
                self.title = self.text
                
            elif name == "page":
                parseArticle(self.title, self.text)
            
        def characters(self, ch):
            if self.chflag :
                self.text +=  ch

    saxparser = make_parser()
    saxparser.setContentHandler(myHandler())

    datasource = open(dump_path, "r")
    saxparser.parse(datasource)


if __name__ == '__main__':
    sys.exit(extract_syn("/home/yk/Downloads/frwiktionary-20150321-pages-articles.xml"))