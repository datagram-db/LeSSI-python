import sys

import yaml

from crawltogsm.CrawlToGSM import CrawlToGSM
from newscrawl.scrape_by_keyword import scrape_by_keyword, crawl_from_csv
from newscrawl.generate_final_db import generate_final_db


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


if __name__ == "__main__":
    conf = "config.yaml"
    if (len(sys.argv) >= 2):
        conf = sys.argv[1]
    try:
        with open(conf) as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
            if 'hand_dataset' in cfg:
                cfg['rewritten_dataset'] = 'rewritten_'+cfg['hand_dataset']
    except FileNotFoundError:
        raise Exception("Error: missing configuration file")

    if "news_parser" in cfg:
        s = Struct(**cfg["news_parser"])
        if ("do_news_parser" in cfg) and (cfg["do_news_parser"]):
            scrape_by_keyword(s)
        if "do_crawl_from_csv" in cfg and (cfg["do_crawl_from_csv"]):
            crawl_from_csv(s)
    if "generate_final_db" in cfg and ("news_parser" in cfg and ("db_ph1" in cfg["news_parser"])):
        generate_final_db(cfg["news_parser"]["db_ph1"], cfg["generate_final_db"]["db_ph2"])
    toGSM = CrawlToGSM(cfg)
    toGSM()
