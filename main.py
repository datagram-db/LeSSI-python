import sys

import stanza
import yaml

from crawltogsm.MainPipeline import MainPipeline
from crawltogsm.write_to_log import write_to_log
from gsmtosimilarity.conceptnet.ConceptNet5 import ConceptNetService
from gsmtosimilarity.database.FuzzyStringMatchDatabase import FuzzyStringMatchDatabase
from gsmtosimilarity.geonames.GeoNames import GeoNamesService
from gsmtosimilarity.stanza_pipeline import StanzaService
from newscrawl.NewsCrawl import NewsCrawl

# TODO: your current configuration uses this as a server, right?
#       Then, at initialization phase, we should move the time-consuming
#       initialization at this point, so to reduce the warm-up time
stanza_service = StanzaService()
crawler = NewsCrawl()

# TODO: also add the initialization for the GeoNames resolution.
#       Be warned! It takes a lot of primary memory
geo_names = None
# Temp init locations
# geo_names.no_file_init("Newcastle Upon Tyne", "n/t/uk/e/w")
# geo_names.no_file_init("Tyne and Wear", "t/uk/e/w")
# geo_names.no_file_init("London", "l/uk/e/w")
# geo_names.no_file_init("Rome", "r/l/i/e/w")


# TODO:
concept_net = None
FuzzyStringMatchDatabase.instance()


def start_pipeline(sentences=None, cfg=None):
    if cfg is None:
        conf = "config_proposed.yaml"
        if len(sys.argv) >= 2:
            conf = sys.argv[1]
        try:
            with open(conf) as f:
                cfg = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise Exception("Error: missing configuration file")

    ## DB Initialisation
    (FuzzyStringMatchDatabase
     .instance()
     .init(cfg["db"]["db"], cfg["db"]["uname"], cfg["db"]["pw"], cfg["db"]["host"], cfg["db"]["port"]))
    FuzzyStringMatchDatabase.instance().create("conceptnet", cfg["conceptnet"])
    # FuzzyStringMatchDatabase.instance().create("geonames", cfg["geonames"])
    global geo_names
    geo_names = GeoNamesService()
    global concept_net
    concept_net = ConceptNetService()

    if sentences is None:
        if 'hand_dataset' in cfg:
            cfg['rewritten_dataset'] = 'rewritten_' + cfg['hand_dataset']
    else:
        cfg['sentences'] = sentences
        cfg['rewritten_dataset'] = 'rewritten_user_input'

    write_to_log(cfg, "Starting pipeline...")

    crawler(cfg)
    pipeline = MainPipeline(cfg)
    pipeline.do_sentence_preprocessing()
    pipeline.do_sentence_matching_and_evaluation()

    write_to_log(cfg, "Finished")


if __name__ == "__main__":
    start_pipeline()
