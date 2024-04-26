import sys

from CleanPipeline import CleanPipeline


def start_pipeline(sentences=None, cfg=None):
    if cfg is None:
        conf = "config.yaml"
        if len(sys.argv) >= 2:
            conf = sys.argv[1]
    else:
        conf = cfg

    clean_pipeline = CleanPipeline().instance()
    clean_pipeline.init(conf)
    print(clean_pipeline.run())
    clean_pipeline.write_to_log("Finished")


if __name__ == "__main__":
    start_pipeline()
