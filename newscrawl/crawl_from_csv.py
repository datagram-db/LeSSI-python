#!/usr/bin/env python3
__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2020, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"
# This script can be used when you want to upload all the urls listed in the CSV files into the json dbs.
# This could be done when "scrape_by_keyword" fails during the processing of the RSS feed
import scrape_by_keyword
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape by Keyword: scraping the online news via Python.")
    parser.add_argument("--RSSFeedCsv", default=False, type=str,
                        help="Defines the configuration csv file containing the rss feed from the newspapers")
    parser.add_argument('--threads', default=8, type=int, help="The minimum amount of threads to be used in the scraping")
    args = parser.parse_args()
    scrape_by_keyword.crawl_from_csv(args)
    # scrape_by_keyword.rssFeedFile = args.RSSFeedCsv
    # scrape_by_keyword.workers = args.threads
    # scrape_by_keyword.load_database('db.json')
    # if scrape_by_keyword.workers == 0:
    # 	scrape_by_keyword.get_all_csvs()
    # else:
    # 	scrape_by_keyword.multi_crawl()
    # scrape_by_keyword.dump_database('db.json')
