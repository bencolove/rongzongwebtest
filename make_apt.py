# coding: utf-8
#!/usr/bin/env python


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.common.exceptions import NoSuchElementException
from xvfbwrapper import Xvfb
from datetime import datetime
import subprocess
import logging
import re


def get_result(driver):
    try:
        body_tag = driver.find_element(By.TAG_NAME, 'body')
        # print(body_tag.text)
        return True
    except NoSuchElementException:
        # mat = re.findall('alert\((\S*)\)', driver.page_source)
        # msg = mat[0].replace('\\n\\r', '') if mat else 'No tips'
        # print("Error happens, cause : {}".format(msg))
        if re.findall('alert\(', driver.page_source):
            # alert pops up
            alert = Alert(driver)
            print(alert.text)
            alert.accept()
        return False


def get_pass_num(url):
    rst = subprocess.run(
        'docker exec tesseract bash -c "python3 parse_img.py {}"'.format(url),
        shell=True,
        stdout=subprocess.PIPE)
    b_output = rst.stdout
    if b_output:
        return b_output.decode('utf-8').strip()

def get_date_from_mingguo(time):
    parts = time.split('.')
    return datetime(int(parts[0]) + 1911, int(parts[1]), int(parts[2]))

def find_vacancy(driver, after=None, before=None):
    driver.switch_to.frame('leftFrame')
    # tag for appoitment
    apt_tag = driver.find_element(By.CSS_SELECTOR, 'body > table > tbody > tr:nth-child(3) > td > a')
    apt_tag.click()
    # switch back to mainFrame
    driver.switch_to.parent_frame()
    driver.switch_to.frame('mainFrame')

    # jump to eye department
    eye_dpt_tag = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 
            'body > table:nth-child(13) > tbody > tr:nth-child(5) > td:nth-child(4) > a')))
    eye_dpt_tag.click()

    apt_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
            'body > table:nth-child(77)')))

    trs = apt_table.find_elements(By.TAG_NAME, 'tr')
    # display doc's name
    tr = trs[0]
    name = tr.find_element(By.CSS_SELECTOR, 'td > font > b').text.strip()
    print("Making appoitment with {}".format(name))
    trs = trs[2:]
    for tr in trs:
        tds = tr.find_elements(By.TAG_NAME, 'td')
        try:
            mkapt_tag = tds[0].find_element(By.TAG_NAME, 'a')
            # can make appoitment
            vacancy_day_str = tds[1].text
            print("Found vacancy on {}".format(vacancy_day_str))
            vacancy_day = get_date_from_mingguo(vacancy_day_str)
            if after <= vacancy_day <= before:
                print("Valid vacancy on {}, try to make appointment"
                      .format(vacancy_day_str))
                # jump to form submitting page
                mkapt_tag.click()
        except NoSuchElementException:
            pass

def view_appoitment(driver):
    # display scheduled appoitments
    leftframe(driver)
    view_apt_tag = driver.find_element(
        By.CSS_SELECTOR, 'body > table > tbody > tr:nth-child(4) > td > a')
    view_apt_tag.click()
    mainframe(driver)
    submit_form(driver)


def submit_form(driver):
    print("Try to prepare infomation and submit...")
    # need to wait until numimage pops up
    # locate verification image
    try:
        # we have to wait for the page to refresh, the last thing that seems to be updated is the title
        img_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                'img#numimage[src*="gif"]')))

        # You should see "cheese! - Google Search
    except Exception as e:
        print(e)
    #img_tag = driver.find_element(By.ID, 'numimage')
    img_url = img_tag.get_attribute('src')

    # need to figure out recognization
    num_pass = get_pass_num(img_url)
    print("Verificaiton pass from {} is recognized as {}."
          .format(img_url, num_pass))

    print("Info to send:\n"
          "N126721711\n"
          "100.08.02")

    # prepare form data
    id_input = driver.find_element(By.NAME, 'patientID')
    id_input.send_keys('N126721711')
    yob_input = driver.find_element(By.NAME, 'patientBirthYear')
    yob_input.send_keys('100')
    mob_select = driver.find_element(By.NAME, 'patientBirthMonth')
    mob_select = Select(mob_select)
    mob_select.select_by_visible_text('08')
    dob_select = Select(driver.find_element(By.NAME, 'patientBirthDate'))
    dob_select.select_by_visible_text('02')
    pass_tag = driver.find_element(By.NAME, 'pass')
    pass_tag.send_keys(num_pass)
    form = driver.find_element(By.ID, 'senddata')
    form.submit()
    print("Form submitted.")


def switch_to_frame(driver, frame_name):
    try:
        driver.find_element(By.TAG_NAME, 'frame')
        # on the root html document containing frames
    except NoSuchElementException:
        # not on the root html document
        # jump back to root first
        driver.switch_to.parent_frame()
    driver.switch_to_frame(frame_name)


def leftframe(driver):
    '''switch to left frame
    '''
    switch_to_frame(driver, 'leftFrame')


def mainframe(driver):
    '''switch to main frame
    '''
    switch_to_frame(driver, 'mainFrame')


def dismiss_popup(driver):
    # dismiss popup
    all_windows = driver.window_handles
    if len(all_windows) == 2:
        # a windwo popsup, dismiss it
        current_window = driver.current_window_handle
        popup_window = (set(all_windows) - set([current_window])).pop()
        driver.switch_to_window(popup_window)
        driver.close()
        driver.switch_to_window(current_window)


def visit_home():
    '''must first call this and retrieve a driver
    '''
    # first visit on home should dismiss a popup
    driver = webdriver.Firefox()
    driver.get('http://register.vghtc.gov.tw/register/')
    dismiss_popup(driver)
    return driver


def run():
    driver = webdriver.Firefox()
    #driver = webdriver.Chrome()
    home_url = 'http://register.vghtc.gov.tw/register/'
    driver.get(home_url)

    # find out valid vacancy
    find_vacancy(driver, after=datetime(2017,8,1), before=datetime(2017,8,31))
    # send verification
    parent_frame(driver)
    switch_frame(driver, 'mainFrame')
    apt_sheet = driver.find_element(By.CSS_SELECTOR, 'body > table')
    print(apt_sheet.text)
    send_verification(driver)
    # result
    done = get_result(driver)
    if done:
        print("Appoitment made ! ")
    else:
        print("Failed to make the appoitment !")
    driver.quit()

if __name__ == '__main__':
    #with Xvfb(width=1024, height=768) as xvfb:
    driver = visit_home()
    view_appoitment(driver)
    driver.quit()

