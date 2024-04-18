import sys

from CleanPipeline import CleanPipeline

if __name__ == "__main__":
    conf = "config.yaml"
    if len(sys.argv) >= 2:
        conf = sys.argv[1]
    clean_pipeline = CleanPipeline().instance()
    clean_pipeline.init(conf)
    print(clean_pipeline.run())
    clean_pipeline.write_to_log("Finished")
