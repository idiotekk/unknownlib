import logging

# create logger
log = logging.getLogger('scheme')
log.propagate = False # do not inherit root logger

# create console handler and set level to debug
_handler = logging.StreamHandler()
_handler.setLevel(logging.INFO)

# create formatter
default_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(module)s %(funcName)s - %(message)s',
    datefmt="%Y%m%d %H:%M:%S")

# add formatter to _handler
_handler.setFormatter(default_formatter)

# add _handler to log
log.addHandler(_handler)