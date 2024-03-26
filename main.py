import subprocess
import sys

import yaml

from crawltogsm.MainPipeline import MainPipeline
from newscrawl.NewsCrawl import NewsCrawl


def start_pipeline(sentences=None, cfg=None):
    print("Starting pipeline...")

    if cfg is None:
        conf = "config_proposed.yaml"
        if (len(sys.argv) >= 2):
            conf = sys.argv[1]
        try:
            with open(conf) as f:
                cfg = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise Exception("Error: missing configuration file")

    if sentences is None:
        if 'hand_dataset' in cfg:
            cfg['rewritten_dataset'] = 'rewritten_' + cfg['hand_dataset']
    else:
        cfg['sentences'] = sentences
        cfg['rewritten_dataset'] = 'rewritten_user_input'

    crawler = NewsCrawl()
    crawler(cfg)
    pipeline = MainPipeline(cfg)
    pipeline.do_sentence_preprocessing()
    pipeline.do_sentence_matching_and_evaluation()


if __name__ == "__main__":
    start_pipeline()
