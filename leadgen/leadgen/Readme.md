**# Folder Descriptions**

spiders - folder contains all the spiders

logs - folder contains all the logs produced by spiders

domains - folder contains .txt files that has domains that can be crawled

files - contains both downloaded and parsed files of domains.


**# Files Descriptions**

test_spider.py: flagship crawler that is used by this project

settings.py: settings used by spiders(these settings can be changed even inside the spider file)

pdftext.py: flagship parser of this project used to perform sorting and sort/delete them based on predefined specifications.

config.py: contains download folder and the current domain that's getting crawled/parsed.

run_spiders.py: orchestrates the pipeline, takes .txt file containing domain name as input, then runs spider and once after the parsing is finished it runs the parser on what's downloaded.

# Files that require incorporation into the software in the future and are currently used manually:

deleteEmptyFolders.py: Deleted empty folders that contain no files used for deleting empty folders, reducing the manual lookup time.

parsing.py: takes pdf file as input and shows where the leads are located in the pdf, reducing the manual pdf lookup time.

bs.py: cleans domain names and writes them into an excel file
