import sys
#
# import stanza
# import yaml

from CleanPipeline import CleanPipeline
# from crawltogsm.LegacyPipeline import LegacyPipeline
# from crawltogsm.write_to_log import write_to_log
# from gsmtosimilarity.conceptnet.ConceptNet5 import ConceptNetService
# from gsmtosimilarity.database.FuzzyStringMatchDatabase import FuzzyStringMatchDatabase
# from gsmtosimilarity.geonames.GeoNames import GeoNamesService
# from gsmtosimilarity.stanza_pipeline import StanzaService
# from newscrawl.NewsCrawl import NewsCrawl


def start_pipeline(sentences=None, cfg=None):
    conf = "config.yaml"
    if len(sys.argv) >= 2:
        conf = sys.argv[1]
    clean_pipeline = CleanPipeline().instance()
    clean_pipeline.init(conf)
    print(clean_pipeline.run())
    from crawltogsm.write_to_log import write_to_log
    clean_pipeline.write_to_log("Finished")

if __name__ == "__main__":
    start_pipeline()
