import subprocess
import sys

import yaml


def write_to_log(cfg, text):
    with open(f"{cfg['web_dir']}/log.txt", 'w') as f:
        f.write(f"{text}")
        f.close()


from crawltogsm.MainPipeline import MainPipeline
from newscrawl.NewsCrawl import NewsCrawl


def start_pipeline(sentences=None, cfg=None):
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

    write_to_log(cfg, "Starting pipeline...")

    crawler = NewsCrawl()
    crawler(cfg)
    pipeline = MainPipeline(cfg)
    pipeline.do_sentence_preprocessing()
    pipeline.do_sentence_matching_and_evaluation()

    write_to_log(cfg, "Finished")


if __name__ == "__main__":
    start_pipeline()
