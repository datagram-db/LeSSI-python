import sys

from CleanPipeline import CleanPipeline


def start_pipeline(cfg=None):
    if cfg is None:
        conf = "config.yaml"
        if len(sys.argv) >= 2:
            conf = sys.argv[1]
    else:
        conf = cfg
    clean_pipeline = CleanPipeline().instance()
    clean_pipeline.init(conf, False)
    clean_pipeline.cfg['hand_dataset'] = "test1"
    # print(clean_pipeline.run())
    clean_pipeline.write_to_log("Finished")
    clean_pipeline.fromExternalSentences("/home/giacomo/Scaricati/test(2).json")


if __name__ == "__main__":
    start_pipeline()
