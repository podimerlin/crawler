import xlrd
import xlsxwriter

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

from datetime import datetime

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

def get_listing_page_of_agent(agent_info):
    # http://www.propertyguru.com.sg/property-agent-directory/search?q=Alice+Yap&listings=
    print 'Looking for %s...' %agent_info[0]
    agent_name = agent_info[0].strip().replace(' ','+')

    agent_search_query = "http://www.propertyguru.com.sg/property-agent-directory/search?q=" + agent_name + "&listings="

    agent_search_browser = webdriver.Chrome("./chromedriver.exe")
    agent_search_browser.get(agent_search_query)
    WebDriverWait(agent_search_browser, 120).until(EC.presence_of_element_located((By.ID, "copy")))

    while(True):
        if 'want to make sure' in agent_search_browser.page_source.encode('utf-8'):
            print 'need help with captcha !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            time.sleep(5)
        else:
            break
    WebDriverWait(agent_search_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))

    agent_search_result_html = html.fromstring(agent_search_browser.page_source)

    agent_found = agent_search_result_html.cssselect("div.alisting_item")

    agent_search_browser.quit()
    
    result = 'Cannot Find %s!' %agent_info[0]

    if len(agent_found) == 0:
        return result

    for agent in agent_found:
        if str(agent_info[2])[0:8] in html.tostring(agent):
            agent_page_link = get_link_from_html_element(agent)
            agent_info_page = "http://www.propertyguru.com.sg" + agent_page_link
            print 'Found! %s' %agent_info_page
            return agent_info_page
        else:
            continue
        '''
        temp_browser = webdriver.Chrome("./chromedriver.exe")
        temp_browser.get(agent_info_page)
        WebDriverWait(temp_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))
        while(True):
            if 'want to make sure' in temp_browser.page_source.encode('utf-8'):
                print 'need help with captcha'
                time.sleep(5)
            else:
                break
        WebDriverWait(temp_browser, 30).until(EC.presence_of_element_located((By.ID, "copy")))

        agent_info_page_html = html.fromstring(temp_browser.page_source)
        agent_verify_info_html = agent_info_page_html.cssselect("div.summary2")
        all = ''
        for each in agent_verify_info_html:
            all += html.tostring(each)
        if agent_info[1] in all and str(agent_info[2])[0:8] in all:
            print all
            result = temp_browser.current_url
            temp_browser.quit()
            break
        temp_browser.quit()
        '''

    print result
    return result

book = xlrd.open_workbook('C.xlsx')
sheet = book.sheet_by_index(0)

backupfile = 'listing-backup-' + datetime.now().strftime("%d%m%y") + '.txt'

print 'Starting...'
print 'Backup File = %s' %backupfile

agent_list = []
count = 0
while(True):
    try: 
        agent_list.append(sheet.row_values(count))
    except IndexError:
        break
    finally:
        count += 1

# print agent_list[count-1][0]
for agent in agent_list:
    if agent[0] == 'Name': continue
    
    url = get_listing_page_of_agent(agent)
    
    w = open(backupfile,'a+')
    w.write('%s,%s\n' %(agent[1], url))
    w.close()

with open(backupfile) as f:
    agent_list = f.readlines()

book_for_write = xlsxwriter.Workbook('listing_page.xlsx')
sheet_for_write = book_for_write.add_worksheet()

j = 0

for agent in agent_list:
    sheet_for_write.write(j-1,0,agent.split(',')[0])
    sheet_for_write.write(j-1,1,agent.split(',')[1])
    #sheet_for_write.write(j-1,0,agent_list[j][1])
    #sheet_for_write.write(j-1,1,agent_list[j][-1])
    j += 1
    
book_for_write.close()

print 'Done'

