import urllib, urllib2, json, os, datetime
from BeautifulSoup import BeautifulSoup
import HTMLParser
    
html_parser = HTMLParser.HTMLParser()
today = str(datetime.datetime.now().date())

# rent, sale 
category = ['rent', 'rooms']
#category = ['sale']

type = 'rental' if 'rent' in category else 'sale'

base_url = 'https://www.99.co'

def populate_links(url):
    print url

    response = urllib2.urlopen(url)
    tempLink = []

    for line in response:
        if any('href="/singapore/%s/listings' %word in line for word in category):
            hit = line.strip()
            link = hit.split('href="')[1].split('"')[0]
            #print link
            
            tempLink.append(link.strip())

    return(list(set(tempLink)))
    
def record(file, data):
    f = open('%s/%s/%s.json' %(today,type,file), 'a+')
    f.write(data)
    f.close()

print 'Welcome to the 99 crawler!'
print 'Initializing... Type: %s' %type

if not os.path.exists(today+"/"+type):
    os.makedirs(today+"/"+type)
    

print '\nOutput folder [%s/%s]\n' %(today,type)
print 'Reading CEA from file N.txt...'

with open('N.txt') as f:
    uid_list = f.readlines()

print '%s CEA(s) found! Starting crawler...' %len(uid_list)

#uid_list = ['R043352J']    
#uid_list = ['R011994Z']

for uid in uid_list:

    uid = uid.strip()
    print '\nCrawling cea %s =====' %uid
    
    links = []

    url = "%s/agents/%s" %(base_url, uid)
    links = populate_links(url)

    print category, '-', len(links), 'found'
    
    result = []
    for link in links:
        p = {}
        url = "%s%s" %(base_url, link)
        
        response = urllib2.urlopen(url)
        data = response.read()
        
        parsed_html = BeautifulSoup(data)
        
        #image id: gallery-overview
        
        # get details
        title_container = parsed_html.find('div', 'pure-u-1 pure-u-lg-15-24')
        detail_container = parsed_html.find('div', attrs={'id':'detail-container'})
        key_detail = detail_container.find('div', 'section-wrapper listing_details')
        amen_details = detail_container.find('div', 'section-wrapper listing_amenities')
        desc_container = detail_container.find('div', 'section-wrapper description')
        
        photos_container = parsed_html.find('div', attrs={'id':'gallery-overview'})
        
        # Title
        name = title_container.find('h1', 'h3 text-left').text
        address = title_container.find('p').text
        price = title_container.find('h2', 'h4 fw-500').text
        
        unit_details = title_container.findAll('h2', 'p')
        
        p['name'] = name 
        p['address'] = address.split('-')[0]
        p['type'] = address.split('-')[1]
        p['price'] = price
        
        d = {}
        for u in unit_details:
            label = u.find('span', 'p').text
            text = u.find('span', 'fw-600')
            if text:
                text = text.text
            else:
                text = u.find('span', 'fw-6yep00').text

            d[label] = text
        
        # Key Details
        key_details = key_detail.findAll('div', 'pure-g')
        key_items = key_details[1].findAll('p')
        for item in key_items:
            label = item.text.split(":")[0]
            text = item.text.split(":")[1]
            
            d[label] = text
        
        # Amenities
        features = []

        try:
            amenities = amen_details.findAll('div', 'pure-u-1')
            amen_items = amenities[1].findAll('div', 'pure-u-1 pure-u-lg-1-2')
            for item in amen_items:
                features.append(item.text)
        except:
            features = []
                
        # Description
        try:
            desc = desc_container.find('p', attrs={'id':'description-text'}).text
            desc = desc.encode('utf-8')
        except:
            desc = ""
            
        # Photo
        photo_url = []
        photos = photos_container.findAll('div', 'gallery-photo')
        for photo in photos:
            #purl = photo.split('data-full="')[1].split('"')[0]
            purl = photo['data-full']
            photo_url.append(str(purl))
            
        p['details'] = d
        p['features'] = features
        p['desc'] = desc
        p['photos'] = photo_url
        
        #print p
        result.append(p)
        
        print 'processing cea %s, %s' %(uid, name)

    pretty_result = json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))
    
    record(uid ,pretty_result)

    print 'Done.. moving to next..'
   
print '\nNo more! Terminating'
