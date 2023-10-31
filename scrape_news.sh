#!/bin/bash
#rm -rf *.csv
./scrape_by_keyword.py --RSSFeedCsv "newcastle.txt" --back_archive --min_date 2023-09-01 --threads 8 --shuffle --reverse --no_ssl --store_json && ./crawl_from_csv.py --RSSFeedCsv newcastle.txt && ./generate_final_db.py &&  rm *.csv
#python3 02_crawl_from_csv.py
#rm -rf *.csv


