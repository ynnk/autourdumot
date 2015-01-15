import urllib2
from pyquery import PyQuery as pq
from  urllib import quote
    

def get_arg(path):
    args = [ i for i in path.split('/') if not i == ""]
    return args[-1]

def _pyquery_opener(url):
    """ set special user agent to trick wiktionary and prevent 403"""
    #see http://www.diveintopython.org/http_web_services/user_agent.html
    request = urllib2.Request(url) 
    request.add_header('User-Agent', 'OpenAnything/1.0') 
    opener = urllib2.build_opener()

    xml = opener.open(request).read()
    xml = xml.replace(' xmlns=', ' ns=') # hack  namespace lxml bug

    return xml.decode('utf8')


def get_wk_definition(domain, query):
    
    useless = ('#contentSub', '#siteSub' ,'#jump-to-nav', '#toc', '#catlinks', '.printfooter', '.visualClear', '.editsection')
    
    url = "http://%s.wiktionary.org/wiki/%s" % (domain, quote(query))
    p = pq(url=url, opener=_pyquery_opener) # using special opener to trick user agent
    definition = p('#bodyContent')
    
    # removes useless data
    for i, e in enumerate(useless):
        definition.remove(e) 
    
    # change links to open in new window
    for link in definition.find('a'):
        pq(link).attr('target' , '_blank')
        href = pq(link).attr('href')
        if href[0] != "#" and href[0:4] != "http" : # not an anchor or external link
            pq(link).attr('href', domain + href)
    
    # fix img src url
    for img in definition.find('img'):
        src = pq(img).attr('src')
        if src[0] == "/" and not src[1] == "/": 
            pq(img).attr('src', domain + src)
    
    # add title and infos
    #definition.prepend("<h1>%s</h1>"%(query) )
    #definition.prepend("Definition taken from %s.wiktionary.org : <a href='%s' target='_blank'>%s</a> "%(domain, url, query) )
    
    return  { 'domain': domain,
              'url' : url,
              'query' : query,
              'content' : definition.html().encode('utf8'),
            }


