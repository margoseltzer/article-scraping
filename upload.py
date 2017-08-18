import os
from selenium import webdriver
from PIL import Image
from time import sleep
#import urllib
#import urllib2

url = 'http://camflow.org/demo'

# https://stackoverflow.com/questions/15018372/how-to-take-partial-screenshot-with-selenium-webdriver-in-python
try:
  driver = webdriver.Firefox()
  driver.maximize_window()
  driver.get(url)
  driver.find_element_by_id("fileinput").click()
  driver.find_element_by_css_selector('input[type="file"]').send_keys(os.getcwd()+"/output.json")
except:
  # close the firefox one
  driver.quit()

  # https://stackoverflow.com/questions/8255929/running-selenium-webdriver-python-bindings-in-chrome
  chromedriver = "/home/ychinlee/Downloads/chromedriver"
  driver = webdriver.Chrome(chromedriver)
  driver.maximize_window()
  driver.get(url)
  driver.find_element_by_id("fileinput").click()
  driver.find_element_by_css_selector('input[type="file"]').send_keys(os.getcwd()+"/output.json")
  
sleep(2)

element = driver.find_element_by_xpath('//div[@style="-webkit-tap-highlight-color: rgba(0, 0, 0, 0); position: relative; z-index: 0; overflow: hidden; width: 800px; height: 600px;"]')
#element = driver.find_element_by_xpath('//div[@style="position: relative; z-index: 0; overflow: hidden; width: 800px; height: 600px;"]')
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
