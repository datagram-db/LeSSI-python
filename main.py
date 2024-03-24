import sys

import yaml

from crawltogsm.MainPipeline import MainPipeline
from newscrawl.NewsCrawl import NewsCrawl


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

    Crawler = NewsCrawl()
    Crawler(cfg)
    pipeline = MainPipeline(cfg)
    pipeline.do_sentence_preprocessing()
    pipeline.do_sentence_matching_and_evaluation()
