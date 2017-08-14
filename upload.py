import os
from selenium import webdriver
from PIL import Image
import requests
from time import sleep
#import urllib
#import urllib2

url = 'http://camflow.org/demo'

# https://stackoverflow.com/questions/15018372/how-to-take-partial-screenshot-with-selenium-webdriver-in-python
driver = webdriver.Firefox()
driver.get(url)

driver.find_element_by_id("fileinput").click()
#driver.find_element_by_css_selector("input[type=\"file\"]").clear()
#driver.find_element_by_css_selector('input[type="file"]').send_keys("C:\Documents\Summer2017\\article-scraping\output.json")
#driver.find_element_by_css_selector('input[type="file"]').send_keys("home/ychinlee/Documents/Summer2017/article-scraping/output.json")
driver.find_element_by_css_selector('input[type="file"]').send_keys(os.getcwd()+"/output.json")
sleep(2)

#element = driver.find_element_by_xpath('//canvas[@style="user-select"]')
element = driver.find_element_by_css_selector('canvas')
location = element.location
size = element.size
driver.save_screenshot('sshot.png')
driver.quit()
print("got here")

im = Image.open('sshot.png')
left = location['x']
top = location['y']
right = location['x'] + 800#size['width']
bottom = location['y'] + 600#size['height']
print((left, top, right, bottom))

im = im.crop((left, top, right, bottom))
im.save('sshot.png')
print("got here")

driver.quit()
'''
values = {'fileinput':'output.json'}
f = {'fileinput' : open('output.json', 'rb')}
#r = requests.post(url, files = f)
r = requests.post(url, files= f)
# screenshot

'''
