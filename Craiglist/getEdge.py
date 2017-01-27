import urllib, urllib2, json, os, datetime, re, cgi
from BeautifulSoup import BeautifulSoup
import HTMLParser

html_parser = HTMLParser.HTMLParser()
today = str(datetime.datetime.now().date())

commercial_list = ['Shop', 'Office', 'Factory', 'Warehouse']

def populate_links(url, uid):
    response = urllib2.urlopen(url)
    tempLink = []
    regex = 'href=[\'"](/' + re.escape(uid) + '/[^\'"]*)'

    for line in response:
        m = re.search(regex, line)
        if m is not None:
            link0 = m.group(1)

            tempLink.append(link0)

    return(list(set(tempLink)))

def populate_links2(url):
    response = urllib2.urlopen(url)
    tempLink = []
    regex = 'href=[\'"]/search/([\w]*)'

    for line in response:
        m = re.search(regex, line)
        if m is not None:
            link0 = m.group(1)

            tempLink.append(link0)

    return(list(set(tempLink)))

def record(file, data):
    f = open('%s/%s.json' %(today,file), 'a+')
    f.write(data)
    f.close()
  
base_url = 'http://singapore.craigslist.com.sg'
print 'Welcome to the sg craiglist crawler!'
print 'Initializing...'

if not os.path.exists(today):
    os.makedirs(today)

uid_list = populate_links2(base_url)

with open('E.txt') as f:
    notin = f.readlines()

    
print '\nOutput folder [%s]\n' %today

print '%s uid(s) found! Starting crawler...' %len(uid_list)
    
for uid in uid_list:
    if uid in notin:
        pass
    uid = uid.strip()
    print '\nCrawling uid %s =====' %uid
    
    links = []
    
    url = "%s/search/%s" %(base_url, uid)
    print 'scanning : %s' %(url)
    links = links + populate_links(url, uid)

    result = []
    for link in links:
        p = {}
        commercial = False
        url = "%s%s" %(base_url, link)
        response = urllib2.urlopen(url)
        data = response.read()
        
        try:
            parsed_html = BeautifulSoup(data)
        except:
            pass

        # get details
        # detail_container = parsed_html.find('div', 'tab-content property-detail-page')
        # detail_top = detail_container.find('div', 'row top')
        # detail_top_left = detail_top.find('div', 'col-sm-6')
        # detail_top_right = detail_top.find('div', 'col-sm-6 details-sections')


        title = parsed_html.find(id="titletextonly")
        postingbody = parsed_html.find(id="postingbody")
        postid = parsed_html.find('div', 'postinginfos')

        regex2 = 'post id: ([\d]*)'        

        if postid is not None:
            m2 = re.search(regex2, unicode(postid))
            postid = m2.group(1)

        if title is not None:
            m3 = re.search('>([^<]*)</', unicode(title))
            title = m3.group((1))
        
        p['postid'] = postid
        p['title'] = title
        p['postingbody'] = unicode(postingbody)

        result.append(p)
        
        print 'processing uid %s, cea %s, %s' %(uid, postid, title)
        
    pretty_result = json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))
    
    record(uid ,pretty_result) 
    print 'Done.. moving to next..'
        
print '\nNo more! Terminating'