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

def record(data):
    f = open('agent140116.txt', 'a+')
    f.write(data + '\n')
    f.close()

def get_agency(alpha = None):
    if not alpha:
        #alpha = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','#']
        alpha = []
    else:
        alpha = eval(alpha)

    list_browser = webdriver.Chrome("./chromedriver.exe")
    list_browser.get("https://www.cea.gov.sg/cea/app/newimplpublicregister/publicregister.jspa")
    
    WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.ID, "alphaA")))
    
    for i,index in enumerate(alpha):
        print '================= Agency Index', index
        list_browser.find_element_by_id("alpha" + index).click()
        
        if i > 0: time.sleep(5)
            
        WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "eaLink")))
        
        resultDiv = list_browser.find_element_by_id("resultDiv")
        tbody = resultDiv.find_element_by_tag_name("tbody") # get table body  
        
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        for col in rows:
            agency = col.find_element_by_class_name("eaLink")
            agency.click()

            time.sleep(3)
            
            #print "switch to window", list_browser.window_handles[1]
            list_browser.switch_to_window(list_browser.window_handles[1])

            while(True):
                WebDriverWait(list_browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "colorfulTable")))
                
                agency_div = list_browser.find_element_by_id("agencyDetail")
                agency_tr = agency_div.find_elements(By.TAG_NAME, "tr")
                agency_name = agency_tr[0].find_elements(By.TAG_NAME, "td")[2].text
                agency_id = agency_tr[1].find_elements(By.TAG_NAME, "td")[2].text
                
                details_div = list_browser.find_element_by_class_name("colorfulTable")
                details_body = details_div.find_element_by_tag_name("tbody")
                details_rows = details_body.find_elements(By.TAG_NAME, "tr")
                print agency_name, agency_id
                for col in details_rows:
                    td = col.find_elements(By.TAG_NAME, "td")
                    cea = td[0].text
                    name = (td[1].text).split(' - [')[0]
                    data = "%s;%s;%s;%s" %(cea, name, agency_name, agency_id) #cea,name,agency,agency id
                    record(data)
                
                try:
                    next = list_browser.find_element_by_link_text('next')
                    next.click()
                    time.sleep(5)
                except:
                    break
                
            list_browser.switch_to_window(list_browser.window_handles[0])

## start

print 'Starting..'

get_agency()

print 'Done'






























