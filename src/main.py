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
            logger.record("Error scraping, is type [" + html.info().get_content_type() + "]:\t\t" + website_url)
            return ""
    except:
        logger.record("Error opening:\t\t" + website_url)
        return ""

    logger.record("Scraping:\t\t" + website_url)

    # Strip out all scripting and style elements
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()

    # Strip out unnecessary whitespace
    page_text = soup.get_text()
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


#TODO: Find a way to make these not global variables
#TODO: Currently it treats "https://url.com" and "https://url.com/" as separate urls, fix this
#TODO: Some website have a pinterest / twitter facebook share button that has the tag
#           href="//www.url.com?u=http://real_website.com"
#       Which throws off the program because of the double slashes, trying to combat this with FIX_1
crawled_urls = []
url_list = []
def crawler(url, domain):
    try:
        # Try and open the website,
        # however if that does not work or it is not an html file,
        # throw an exception
        html = urlopen(url)
        if 'text/html' != html.info().get_content_type():
            logger.record("Error crawling, is type [" + html.info().get_content_type() + "]:\t\t" + url)
            crawled_urls.append(url)
            return ""
    except:
        logger.record("Error crawling:\t\t" + url)
        return

    logger.record("Crawling:\t\t" + url)
    soup = BeautifulSoup(html, 'html.parser')           # Put it inside the BeautifulSoup parser

    crawled_urls.append(url)                            # Add the current parsed url to the crawled_urls list
    urls = soup.findAll("a")                            # Search for all "a" tags in the HTML

    # Iterate through all of the "a" tags in the text
    for a in urls:
        stripped_url = str(a)

        # Check if the a tag has a link
        if ("href" in stripped_url):
            stripped_url = stripped_url[stripped_url.find('href')+6:]
            stripped_url = stripped_url[:stripped_url.find('"')]

            #TODO: FIX_1
            # Trying to avoid url stubs starting with "//"
            try:
                if stripped_url == '/' or (stripped_url[0] == '/' and stripped_url[1] == '/'):
                    continue
            except:
                logger.record("Short Url:\t\t" + stripped_url)

            # If the url is a stub, add the base url to the beginning
            if (stripped_url[0] == '/'):
                base_url = "http://" + domain
                stripped_url = base_url + stripped_url

            # If the url is not in the list already, add it
            if (stripped_url not in url_list):
                url_list.append(stripped_url)
            else:
                continue

    # Parse all of the urls in the url list
    for page in set(url_list):

        # Check if the url belong to the same domain
        # And if this url is already parsed ignore it
        if (urlparse(page).netloc == domain) and (page not in crawled_urls):
            # Recursively crawl through
            crawler(page, domain)

        # If the url has been crawled before or is not part of the base domain, skip
        else:
            continue

    # Once all urls are crawled, exit the function
    return


def main():
    websites = []
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
        # Crawl through the urls of the domain
        domain = urlparse(site).netloc
        crawler(site, domain)
        list_of_urls = url_list
        list_of_crawled_urls = crawled_urls

        # Iterate through all of the crawled urls
        for url in set(list_of_urls):
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
        crawled_urls.clear()
        url_list.clear()

    # Close out of results.csv file
    csv.close()


# Run the program
logger = Logger("../res/log.txt")       # Creates the logger global variable
start_time = time.time()                # Used to record the total duration of the script
main()                                  # Run the main method
logger.record("\nRun time - " + str(round((time.time() - start_time), 3)) + " seconds")
logger.save()                           # Save the log
