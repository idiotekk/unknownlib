import logging

# create logger
log = logging.getLogger('scheme')
log.propagate = False # do not inherit root logger

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(module)s %(funcName)s - %(message)s',
    datefmt="%Y%m%d %H:%M:%S")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to log
log.addHandler(ch)