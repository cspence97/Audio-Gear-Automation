# TODO
#  -fix links for featured listings returned when there are no other listings

import math
import time

import joblib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from re import sub
from decimal import Decimal

# Create three text files for easy access/storage to our desired information
f, mf, bf = open('cheapest.txt', 'w'), open('cheap.txt', 'w'), open('broken.txt', 'w')
username = ''
password = ''
timer = 0.0


def main():
    global username, password, timer
    timer = time.monotonic()
    # Prompt for login information
    print("Enter reverb.com credentials: ")
    while True:
        a = input("Use saved credentials? Y/N: ")
        if a.lower() == "y":
            try:
                username, password = joblib.load('user.joblib'), joblib.load('pass.joblib')
                break
            except FileNotFoundError:
                print("No saved credentials found.  Please enter your credentials.")
                username = input("Username: ")
                password = input("Password: ")
                while True:
                    b = input("Save credentials for next time? Y/N: ")
                    if b.lower() == "y":
                        joblib.dump(username, "user.joblib")
                        joblib.dump(password, "pass.joblib")
                        break
                    elif b.lower() == "n":
                        break
                break
        elif a.lower() == "n":
            username = input("Username: ")
            password = input("Password: ")
            while True:
                b = input("Save credentials for next time? Y/N: ")
                if b.lower() == "y":
                    joblib.dump(username, "user.joblib")
                    joblib.dump(password, "pass.joblib")
                    break
                elif b.lower() == "n":
                    break
            break

    # prompt for using previously collected links.  Saves time if
    while True:
        a = input("update links? Y/N: ")
        if a.lower() == "y":
            links = getSiteLinks()
            joblib.dump(links, 'links.joblib')
            break
        elif a.lower() == 'n':
            try:
                links = joblib.load('links.joblib')
            except FileNotFoundError:
                while True:
                    b = input("No links found, collect links? Y/N: ")
                    if b.lower() == "y":
                        links = getSiteLinks()
                        joblib.dump(links, 'links.joblib')
                        break
                    elif b.lower() == "n":
                        elapsedTime()
                        exit()
            break

    # prompt user to see if we should compare prices
    while True:
        a = input("compare current listing prices? Y/N: ")
        if a.lower() == "y":
            scrape(links)
            break
        if a.lower() == "n":
            break

    f.close()
    mf.close()
    bf.close()
    elapsedTime()


# find elapsed time and display it in easy to read format
def elapsedTime():
    endTime = time.monotonic() - timer
    hours = math.floor(endTime / 60 / 60)
    minutes = math.floor((endTime - (hours * 60 * 60)) / 60)
    seconds = math.floor(endTime % 60)

    print("\nTime elapsed: " + str(hours) + ":" + str(minutes) + ":" + str(seconds))


# returns list of links to check pricing
def getSiteLinks():
    # open reverb.com in chrome with webdriver
    DRIVER_PATH = '/usr/local/bin/chromedriver'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    driver.get("https://reverb.com/signin")
    driver.implicitly_wait(10)
    time.sleep(5)

    # account needed to see price guide
    login_username = driver.find_element_by_id('user_session_login')
    login_username.send_keys(username)
    login_password = driver.find_element_by_id('user_session_password')
    login_password.send_keys(password)
    login_password.send_keys(Keys.RETURN)

    delay = 7
    try:
        WebDriverWait(driver, delay).until(ec.presence_of_element_located((By.CLASS_NAME, 'site-header__avatar')))
    except TimeoutException:
        print("Loading took too much time!")

    driver.get("https://reverb.com/price-guide/pro-audio")

    # wait for the page to fully load
    delay = 6
    try:
        WebDriverWait(driver, delay).until(
            ec.presence_of_element_located((By.CLASS_NAME, 'product-card-img-container')))
    except TimeoutException:
        print('took too long')

    # scroll through pages and collect links for all items
    pages = 59
    listings = []
    for i in range(0, pages):  # 60 pages total
        links = driver.find_elements_by_tag_name('a')
        for link in links:
            link = str(link.get_attribute('href'))
            if 'price-guide' and '/guide' in link:
                listings.append(link)
        nextPage = driver.find_element_by_link_text('Next')
        nextPage.click()

    return listings


# scours reverb.com's price guide items and finds those priced lower than usual
def scrape(links):
    count = 0
    DRIVER_PATH = '/usr/local/bin/chromedriver'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    driver.get("https://reverb.com/signin")

    # account needed for price guide
    login_username = driver.find_element_by_id('user_session_login')
    login_username.send_keys(username)
    login_password = driver.find_element_by_id('user_session_password')
    login_password.send_keys(password)
    driver.implicitly_wait(23)
    login_password.send_keys(Keys.RETURN)

    # make sure we're fully logged in
    delay = 5
    try:
        WebDriverWait(driver, delay).until(ec.presence_of_element_located((By.CLASS_NAME, 'site-header__avatar')))
    except TimeoutException:
        print("Loading took too much time!")

    # cycle through items in price guide
    for link in links:
        count += 1
        print("listing: " + str(count) + "/" + str(len(links)), "progress: " + str(100*count/len(links)) + "%")
        time.sleep(1)
        driver.get(link)

        # check for recent listings, crashes without this
        delay = 3
        try:
            WebDriverWait(driver, delay).until(ec.presence_of_element_located((By.CLASS_NAME, 'date')))
        except TimeoutException:
            continue

        # find the link to current listings for item
        addresses = driver.find_elements_by_tag_name('a')
        URL = ''
        for address in addresses:
            url = str(address.get_attribute('href'))
            if '/p/' in url:
                if ' 0 ' in address.text:  # break for loop and ignore url declaration if listing link says 0 listings
                    break
                URL = url

        # ignore pages with no active listings
        if URL == '':
            continue

        # Average the prices from last 10 transactions and compare the current listings
        prices = driver.find_elements_by_class_name('price-history-table-price')
        priceCounter, counter = 0, 0
        for price in prices:
            priceCounter += Decimal(sub(r'[^\d.]', '', price.text))
            counter += 1
        checkListings((priceCounter / counter), URL, driver)


# opens link containing all listings and compare it to the average price; inherits active instance of webdriver
def checkListings(avgPrice, url, driver):
    driver.get(url)

    # grabs all listings and gives em the price guide name
    name = driver.find_element_by_class_name('csp2-header__title').text
    prices = driver.find_elements_by_class_name('price-with-shipping__price__amount')
    urls = driver.find_elements_by_class_name('listing-row-card__inner')
    conditions = driver.find_elements_by_class_name('condition-indicator__label')

    # iterate across listings and compare to avg price
    for i in range(len(prices)):
        p = prices[i]

        # Featured listing url css class different than rest of listings but price isn't so it's one smaller than prices
        if i != 0:
            URL = urls[i - 1]
        else:
            URL = driver.find_element_by_tag_name('a')  # TODO change this to xpath and find proper link

        # compare data and record discounts
        p = Decimal(sub(r'[^\d.]', '', p.text))
        if conditions[i].text not in ["Non Functioning", "Poor", "Fair"]:
            if p < (avgPrice * Decimal(0.75)):  # cheapest
                f.write(name +
                        "\nAverage Price: " + str(avgPrice) +
                        "\nlisting price: " + str(p) +
                        "\nDiscount: " + str((1 - (p / avgPrice))*100) + "%" +
                        "\nURL: " + URL.get_attribute('href') +
                        "\n\n")
            elif (avgPrice * Decimal(0.75)) <= p < (avgPrice * Decimal(0.9)):  # cheap
                mf.write(name +
                         "\nAverage Price: " + str(avgPrice) +
                         "\nlisting price: " + str(p) +
                         "\nDiscount: " + str((1 - (p / avgPrice))*100) + "%" +
                         "\nURL: " + URL.get_attribute('href') +
                         "\n\n")
        else:
            if p < (avgPrice * Decimal(0.6)):  # damaged/broken
                bf.write(name +
                         "\nAverage Price: " + str(avgPrice) +
                         "\nlisting price: " + str(p) +
                         "\nDiscount: " + str((1 - (p / avgPrice))*100) + "%" +
                         "\nURL: " + URL.get_attribute('href') +
                         "\n\n")


if __name__ == '__main__':
    main()
