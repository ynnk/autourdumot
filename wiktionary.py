import re
import requests
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



def get_wk_definition(domain, query):
        
    base_url = "http://%s.wiktionary.org" % domain
    url = "%s/wiki/%s" % (base_url, quote(query))
    
    p = pq(url=url, opener=_pyquery_requests_opener)
    content = p('#bodyContent').html()

    # clean ids
    ids_to_replace = {
        ".C3.A9" : "e"
    }

    for k,v in ids_to_replace.iteritems():
        content = content.replace(k,v)

    # removes useless data
    useless = ('#contentSub', '#siteSub' ,'#jump-to-nav', '#toc', '#catlinks', '.printfooter', '.visualClear', '.editsection',# section edit
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
        #print href
        if href[0] != "#" and href[0:4] != "http" : # not an anchor or external link
            pq(link).attr('target' , '_blank')
            pq(link).attr('href', base_url + href)
    
    # fix img src url
    for img in definition.find('img'):
        src = pq(img).attr('src')
        if src[0] == "/" and not src[1] == "/": 
            pq(img).attr('src', domain + src)

    # 
    
    # add title and infos
    #definition.prepend("<h1>%s</h1>"%(query) )
    #definition.prepend("Definition taken from %s.wiktionary.org : <a href='%s' target='_blank'>%s</a> "%(domain, url, query) )
    
    return  { 'domain': domain,
              'url' : url,
              'query' : query,
              'content' : definition.html().encode('utf8'),
            }


