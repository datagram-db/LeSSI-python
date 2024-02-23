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
import json, os

if __name__ == '__main__':
  db = {}
  files = [f for f in os.listdir('.') if os.path.isfile(f)]
  for f in files:
        if (f.endswith('.json')) and (not (f == "db.json") and not (f == "final_db.json")):
            print(f)
            try:
              l = json.load(open(f))
              for k in l:
               db[l[k]["url"]] = l[k]
            except:
              print("Error on "+f)
  print(str(len(db))+" articles were downloaded in total!")
  json.dump(db,open("final_db.json","w"), indent=4, sort_keys=True)
