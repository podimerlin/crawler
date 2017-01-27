import urllib, urllib2, json, os, datetime
from BeautifulSoup import BeautifulSoup
import HTMLParser

html_parser = HTMLParser.HTMLParser()
today = str(datetime.datetime.now().date())

commercial_list = ['Shop', 'Office', 'Factory', 'Warehouse']
types = ['rental', 'room_rental']
#types = ['room_rental']

def populate_links(url):
    response = urllib2.urlopen(url)
    tempLink = []
    for line in response:
        if 'href="/listing/' in line:
            hit = line.strip()
            link = hit.split('href="')[1].split('">')[0]
            tempLink.append(link)

    return(list(set(tempLink)))

def record(file, data):
    f = open('%s/%s.json' %(today,file), 'a+')
    f.write(data)
    f.close()
  
base_url = 'http://www.theedgeproperty.com.sg'
print 'Welcome to the edge crawler!'
print 'Initializing...'

if not os.path.exists(today):
    os.makedirs(today)
    
print '\nOutput folder [%s]\n' %today
print 'Reading uid from file E.txt...'

with open('E.txt') as f:
    uid_list = f.readlines()

print '%s uid(s) found! Starting crawler...' %len(uid_list)
    
for uid in uid_list:
    #uid = '97825620'
    uid = uid.strip()
    print '\nCrawling uid %s =====' %uid
    
    links = []
    for type in types:
        url = "%s/users/%s?total_per_page=100&listing_type=%s" %(base_url, uid, type)
        links = links + populate_links(url)

    result = []
    for link in links:
        p = {}
        commercial = False
        url = "%s%s" %(base_url, link)
        response = urllib2.urlopen(url)
        data = response.read()
        
        parsed_html = BeautifulSoup(data)
        
        # get details
        detail_container = parsed_html.find('div', 'tab-content property-detail-page')
        detail_top = detail_container.find('div', 'row top')
        detail_top_left = detail_top.find('div', 'col-sm-6')
        detail_top_right = detail_top.find('div', 'col-sm-6 details-sections')
        
        details = detail_top_right.findAll('div', 'property-field-data')

        # details
        details_list = {}
        for detail in details:
            #d = {}
            label = detail.find('label', 'label-inline').text
            text = (detail.text).split(label)[1]
            
            if any(x in text for x in commercial_list):
                commercial = True
                break
            
            #print label, text
            #d[label] = text
            details_list[label] = text
            
        if commercial:
            print 'Commercial Rental.. PASS'
            continue
        
        agent_id = (parsed_html.find('div', 'agent-id section-info').find('span').text).strip()
        
        # get title
        title_container = parsed_html.find('div', attrs={'id':'property-listing-header'})
        title_container1 = title_container.find('div', attrs={'class':'col-sm-8'})
        title_container2 = title_container.find('div', attrs={'class':'col-sm-4 text-right'})
        title_name = title_container1.find('h2').text
        title_address = title_container1.find('div').text
        price = title_container2.find('h2').text
        
        # photos
        photos = []
        for photo in detail_top_left.findAll('img'):
            if 'listing_gallery_full' in photo['src'] and 'amazonaws.com' in photo['src']:
                photos.append(photo['src'])
                #photos.append(photo['src'].split('?')[0])
                #print photo['src'].split('?')[0]

        desc_encoded = parsed_html.find('div', {'id':'prop-desc'})
        
        desc = html_parser.unescape(desc_encoded.text.replace('Property Description', '').replace('<br />', '[breakline]'))
        
        p['name'] = title_name
        p['address'] = title_address
        p['price'] = price
        p['details'] = details_list
        p['photos'] = photos
        p['desc'] = desc
        
        result.append(p)
        
        print 'processing uid %s, cea %s, %s' %(uid, agent_id, title_name)
        
    pretty_result = json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))
    
    record(agent_id ,pretty_result)
    
    print 'Done.. moving to next..'
        
print '\nNo more! Terminating'