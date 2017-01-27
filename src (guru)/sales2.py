import json
import xlrd
from datetime import datetime
from datetime import timedelta
from lxml import html
from lxml.cssselect import CSSSelector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import cookielib
import os
import pickle
import re
import socket
import time
import traceback
import urllib2

'''
rend excel
search by name
verify by phone number and license ID,
    if not equal
    output to log file
    break
    else
    crawl()
'''
def get_link_from_html_element(element):
    link_warpper = html.tostring(element)
    link_start = 4
    link_end = 0
    while(True):
        if link_warpper[link_start] == 'h' and link_warpper[link_start + 1] == 'r' and link_warpper[link_start + 2] == 'e' and link_warpper[link_start + 3] == 'f':
            link_start += 6
            break
        else:
            link_start += 1
    link_end = link_start
    while(True):
        if link_warpper[link_end] == '"':
            break
        else:
            link_end += 1
    link_str = link_warpper[link_start:link_end]
    return link_str

def get_photos_from_html_source(jquery_source):
    # HTTP_LINK_PATTERN = re.compile("^http?://")
    # photo_links = HTTP_LINK_PATTERN.search(jquery_source).groups()
    photo_links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', jquery_source)
    results = []
    for photo_link in photo_links:
        if 'V550.jpg' in photo_link:
            photo_link = photo_link[0:-2]
            results.append(photo_link)
    return results

def get_for_rent_property(agent_list_page):
    # ?items_per_page=50
    # ?smm=3
    print 'Grabbing listings ...'
    meta_str1 = '?items_per_page=50'
    meta_str2 = '?smm='
    list_browser = webdriver.Chrome("./chromedriver.exe")
    list_browser.get(agent_list_page + meta_str1)
    WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))

    while(True):
        if 'want to make sure' in list_browser.page_source.encode('utf-8'):
            print 'need help with captcha'
            time.sleep(5)
        else:
            break

    WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))

    agent_list_page_html = html.fromstring(list_browser.page_source)

    listing_item_elements = agent_list_page_html.cssselect("div.infotitle")
    
    try:
        num_properties = int(agent_list_page_html.cssselect("div.resultFound > font")[0].text_content().strip().replace("\t", "").replace("\n", "").replace("  ",""))
    except:
        num_properties = 0
        
    if num_properties > 50:
        round = 1
        while( 50 * round < num_properties):
            list_browser.get(agent_list_page + meta_str2 + str(round + 1))
            WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))
            while(True):
                if 'want to make sure' in list_browser.page_source.encode('utf-8'):
                    print 'need help with captcha'
                    time.sleep(5)
                else:
                    break
            WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))
            agent_list_page_html = html.fromstring(list_browser.page_source)
            for ele in agent_list_page_html.cssselect("div.infotitle"):
                listing_item_elements.append(ele)
            round += 1

    list_browser.quit()

    keep_these = []
    for element in listing_item_elements:
        if 'For Sale' in element.cssselect("a")[-1].text.strip().replace("\t", "").replace("\n", "").replace("  ",""):
            keep_these.append(element)

    listing_items = []

    temp_browser = webdriver.Chrome("./chromedriver.exe")
    
    print 'No. of sale listings found:', len(keep_these)
    print 'Start Crawling ...'
    for element in keep_these:
        listing_item = {}
        details_page_url = "http://www.propertyguru.com.sg" + get_link_from_html_element(element)
        
        temp_browser.get(details_page_url)
        
        print details_page_url
        
        if 'commercialguru.com' in temp_browser.current_url:
            continue
            
        try:
            WebDriverWait(temp_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))
        except TimeoutException:
            continue

        while(True):
            if 'want to make sure' in temp_browser.page_source.encode('utf-8'):
                print 'need help with captcha'
                time.sleep(5)
            else:
                break
        
        try:
            WebDriverWait(temp_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))
        except TimeoutException:
            continue

        try:
            property_detail_page_html = html.fromstring(temp_browser.page_source)
        except Exception, err:
            print err
            continue
            
        listing_facility = []
        listing_facility_elements = property_detail_page_html.cssselect("ul.listing_facility > li")
        for each in listing_facility_elements:
            if each.attrib.get("original-title"): 
                listing_facility.append(each.attrib["original-title"])
            else: 
                listing_facility.append(each.text_content().strip())
        
        try:
            address = property_detail_page_html.cssselect("div.info1 > p")[-1].text.strip().replace("\t", "").replace("\n", "").replace("  ","")
        except:
            address = ""
        try:
            num_photos = property_detail_page_html.cssselect("li#photo_tab > a")[0].text_content().strip()
        except IndexError:
            num_photos = 0
            pass
        thumbnails_element = property_detail_page_html.cssselect("div.mediathumbnail img") #MAY NEED TO WAIT WILL ALL IMAGES ARE LOADED ACCORDING TO NUMPHOTOS
        photos = []
        for thumbnail in thumbnails_element:
            photos.append(thumbnail.attrib['src'].replace('V75B', 'V550'))

        all = ''
        if num_photos > 0 and int(num_photos[0:2]) != len(photos):
            jquery = property_detail_page_html.cssselect("script")
            for code in jquery:
                all += html.tostring(code)
            photos = get_photos_from_html_source(all)

        has_description = 1
        try:
            description = property_detail_page_html.cssselect("#ldescription")[0].text_content().strip().replace('\n','').replace('\t','')
        except IndexError:
            has_description = 0
        detail_element = property_detail_page_html.cssselect('#detailinfo')[0]
        detail_tds = detail_element.iter("td")
        details = {}
        amenities = []
        for td in detail_tds:
            if ':' in td.text_content():
                details[td.text_content().strip()] = detail_tds.next().text_content().strip().replace('\n','').replace('\t','')
            else:
                amenities.append(td.text_content().strip())
        details['Amenities'] = amenities
        for h3 in detail_element.cssselect("h3.infohead"):
            if ':' in h3.text_content():
                if not details.get(h3.text_content().strip()):
                    details[h3.text_content().strip()] = []
            for li in h3.itersiblings().next().cssselect("li"):
                details[h3.text_content().strip()].append(li.text_content().strip())
        listing_item['address'] = address
        listing_item['num_photos'] = num_photos
        if num_photos > 0:
            listing_item['photos'] = photos
        else:
            listing_item['photos'] = []
        if has_description:
            listing_item['description'] = description
        listing_item['details'] = details
        listing_item['listing_facility'] = listing_facility
        listing_items.append(listing_item)
        time.sleep(0.5)
    temp_browser.quit()
    return listing_items

book = xlrd.open_workbook('listing_page.xlsx')
sheet = book.sheet_by_index(0)

agent_details = []
count = 0
while(True):
    try: 
        agent_details.append(sheet.row_values(count))
    except IndexError:
        break
    finally:
        count += 1

agent_left = []

for agent in agent_details:
    if agent[1] != 'WrongName':
        agent_left.append(agent)

for agent in agent_left:
    print '============================', agent[0]
    results = get_for_rent_property(agent[1])
    temp_file_name = agent[0] + ".json"
    with open(temp_file_name, "w") as f:
        f.write(json.dumps(results, sort_keys=True, indent=4, separators=(',', ': ')))

print 'done'