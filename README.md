# website_keyword_search

#### Requirements
- BeautifulSoup4
- urllib
----
#### Setup
1) Place all of your urls in websites.txt
2) Place all of your keywords in keywords.txt
3) Run the program from the src/ folder
----
#### Regex
Currently the regex does the following changes to the scraped text
- Removes all non-alphabetical characters (such as symbols and numbers)
- Ignores capitalization
- Removes unnecessary whitespace
----
The list of matching websites will be saved in results.csv
