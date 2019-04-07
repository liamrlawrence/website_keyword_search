# ----------------------------------------------------------------------------------
#  File Name    : main.py
#  Description  : Searches for keywords on websites and stores the results in a CSV
#  Authors      : Liam Lawrence
#  Created      : April 6, 2019
#
#  License      : GNU GPL v3
# ----------------------------------------------------------------------------------
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time
import re


#
#
# Params:
#           path: The path of the logging file
# Description:
#           A basic logging class that records everything printed to the console
#
class Logger:
    def __init__(self, path):
        self.path = path
        self.info = ""

    def record(self, message):
        print(message)
        self.info += (message + '\n')

    def save(self):
        f = open(self.path, 'w')
        f.write(self.info)
        f.close()


#
# Params:
#           website_url: The url to the webpage to scrape
#
# Return:
#           The text data from the webpage
#
# Description:
#           Goes through and scrapes an HTML file for any text and returns it
#
def scrape_page(website_url):
    try:
        # Try and open the website,
        # however if that does not work or it is not an html file,
        # throw an exception
        html = urlopen(website_url)
        if 'text/html' != html.info().get_content_type():
            logger.record("Error is type [" + html.info().get_content_type() + "]:\t\t" + website_url)
            return ""
    except:
        logger.record("Error opening:\t" + website_url)
        return ""

    logger.record("Scraping:\t\t" + website_url)

    # Strip out all scripting and style elements
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()

    # Strip out anything that is not an alphabetic character
    page_text = soup.get_text()
    page_text = re.sub(r'[^a-zA-Z ]', '', page_text)

    # Strip out unnecessary whitespace
    lines = (line.strip() for line in page_text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    page_text = '\n'.join(chunk for chunk in chunks if chunk)

    return page_text


#
# Params:
#           url_list:       A list to store all of the urls in
#           crawled_urls:   A list to show which of the urls from url_list has been crawled already
#           url:            The current url being crawled
#           domain:         The main domain of the website, used to make sure the crawler stays on the main website
#
# Return:
#           The filled url_list and crawled_urls lists
#
# Description:
#           Crawls through the website and puts all of the links it can find into lists
#
def crawler(url_list, crawled_urls, url, domain):
    try:
        # Try and open the website,
        # however if that does not work or it is not an html file,
        # throw an exception
        html = urlopen(url)
        if 'text/html' != html.info().get_content_type():
            logger.record("Error is type [" + html.info().get_content_type() + "]:\t\t" + url)
            return ""
    except:
        logger.record("Error crawling:\t" + url)
        return crawled_urls, url_list

    logger.record("Crawling:\t\t" + url)
    soup = BeautifulSoup(html, 'html.parser')           # Put it inside the BeautifulSoup parser

    crawled_urls.append(url)                            # Add the current parsed url to the crawled_urls list
    urls = soup.findAll("a")                            # Search for all "a" tags in the HTML

    # Collect all all urls, however if they are not part of the base domain, ignore them
    for a in urls:
        if (a.get("href")) and (a.get("href") not in url_list):
            url_list.append(a.get("href"))

    # Parse all of the urls from the base domain
    for page in set(url_list):

        # Check if the url belong to the same domain
        # And if this url is already parsed ignore it
        if (urlparse(page).netloc == domain) and (page not in crawled_urls):

            # Recursively crawl through
            crawler(url_list, crawled_urls, page, domain)

    # Once all urls are crawled return the list to calling function
    else:
        return crawled_urls, url_list


def main():
    websites = []
    list_of_urls = []
    list_of_crawled_urls = []
    keywords = []

    # Reads in the data from the input files and
    # gets ready to output the results into a csv
    file = open("../res/websites.txt", 'r')
    for line in file:
        websites.append(line.rstrip())
    file.close()

    file = open("../res/keywords.txt", 'r')
    for line in file:
        keywords.append(line.rstrip())
    file.close()

    csv = open("../res/results.csv", 'w')
    csv.write("Keyword, URL\n")

    # Print the startup message
    logger.record("Websites being used:")
    for site in websites:
        logger.record("\t- " + site)
    logger.record('')
    logger.record("Keywords being used:")
    for word in keywords:
        logger.record("\t- " + word)
    logger.record("")

    # Main loop:
    # Crawl the websites to get the urls, then search
    # each one of those pages for the specified keywords
    for site in websites:
        domain = urlparse(site).netloc
        list_of_crawled_urls, list_of_urls = crawler(list_of_urls, list_of_crawled_urls, site, domain)

        for url in list_of_urls:
            # Appends the base url to the link stubs
            if url[0] == '/':
                url = site + url

            # If the url is part of another website, skip scraping it
            if domain != urlparse(url).netloc:
                continue

            # Scrape the page and parse the text from it
            text = scrape_page(url)

            # Check if any of the keywords are in the scraped text
            # and record the results in a csv file
            for word in keywords:
                regex = r"\b" + re.escape(word) + r"\b"
                if re.search(regex, text, flags=re.IGNORECASE):
                    csv.write(word + ", " + url + '\n')

        # Clean out the url lists for the next website
        list_of_urls.clear()
        list_of_crawled_urls.clear()

    # Close out of results.csv file
    csv.close()


# Run the program
logger = Logger("../res/log.txt")       # Creates the logger global variable
start_time = time.time()                # Used to record the total duration of the script
main()                                  # Run the main method
logger.record("\nRun time - " + str(round((time.time() - start_time), 3)) + " seconds")
logger.save()                           # Save the log
