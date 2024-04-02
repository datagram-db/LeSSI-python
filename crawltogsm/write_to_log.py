def write_to_log(cfg, text):
    if 'web_dir' in cfg and cfg['web_dir'] is not None:
        with open(f"{cfg['web_dir']}/log.txt", 'w') as f:
            f.write(f"{text}")
            f.close()
