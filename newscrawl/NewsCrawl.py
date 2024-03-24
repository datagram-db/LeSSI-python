from crawltogsm.generate_gsm_cypher_db import sentence_preprocessing
from newscrawl.scrape_by_keyword import scrape_by_keyword, crawl_from_csv


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class NewsCrawl:
    def __call__(self, cfg):
        if "news_parser" in cfg:
            s = Struct(**cfg["news_parser"])
            if ("do_news_parser" in cfg) and (cfg["do_news_parser"]):
                scrape_by_keyword(s)
            if "do_crawl_from_csv" in cfg and (cfg["do_crawl_from_csv"]):
                crawl_from_csv(s)
        if "generate_final_db" in cfg and ("news_parser" in cfg and ("db_ph1" in cfg["news_parser"])):
            sentence_preprocessing(cfg["news_parser"]["db_ph1"], cfg["generate_final_db"]["db_ph2"])
