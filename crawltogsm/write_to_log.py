__author__ = "Oliver R. Fox"
__copyright__ = "Copyright 2024, Oliver R. Fox"
__credits__ = ["Oliver R. Fox, Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox"
__status__ = "Production"


def write_to_log(cfg, text):
    from CleanPipeline import CleanPipeline
    CleanPipeline.write_to_log(text)
    # if cfg is not None and 'web_dir' in cfg and cfg['web_dir'] is not None:
    #     with open(f"{cfg['web_dir']}/log.txt", 'w') as f:
    #         f.write(f"{text}")
    #         f.close()
    # else:
    #     print(text)
