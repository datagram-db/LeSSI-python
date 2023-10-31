#!/usr/bin/env python3
__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2020, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"
import scrape_by_keyword

for (x,y) in scrape_by_keyword.url_list(scrape_by_keyword.date_global_minimum.strftime('%Y-%m-%d')):
	scrape_by_keyword.NewsThread(x, scrape_by_keyword.phrases, y, scrape_by_keyword.database, scrape_by_keyword.proxies, True)
