import logging
from copy import copy
from pathlib import Path
from datetime import datetime

### PRETTY COLORS ###

class ColoredFormatter(logging.Formatter):

    color_mapping = {
        'DEBUG':    242, # grey
        'INFO':     69,  # blue
        'WARNING':  208, # orange
        'ERROR':    196, # red
        'CRITICAL': 196, # red
        200:        118, # green
    }

    char_mapping = {
        'DEBUG':    ' * ',
        'INFO':     ' + ',
        'WARNING':  ' - ',
        'ERROR':    ' ! ',
        'CRITICAL': '!!!',
    }

    prefix = '\033[1;38;5;'
    suffix = '\033[0m'

    def __init__(self, pattern):

        super().__init__(pattern)


    def format(self, record):

        colored_record = copy(record)

        response_code = None
        try:
            response_code = int(colored_record.getMessage().split()[0])
        except ValueError:
            pass

        levelname = colored_record.levelname
        levelchar = self.char_mapping.get(levelname, None)
        if response_code is not None:
            levelchar = f'{response_code:003}'
        else:
            levelchar = ' * '
        seq = self.color_mapping.get(response_code, self.color_mapping.get(levelname, 15)) # default white
        colored_levelname = f'{self.prefix}{seq}m[{levelchar}]{self.suffix}'
        colored_record.levelname = colored_levelname

        return logging.Formatter.format(self, colored_record)


### LOG TO STDERR ###

console = logging.StreamHandler()
# tell the handler to use this format
console.setFormatter(ColoredFormatter('%(levelname)s %(message)s'))
root_logger = logging.getLogger('dirspray')
root_logger.handlers = [console]


def log_response(r, levelname=None):

    if levelname is None:
        if 200 <= response.status_code <= 299:
            levelname = 'INFO'
        if 300 <= response.status_code <= 399:
            levelname = 'DEBUG'
        if 400 <= response.status_code <= 499:
            levelname = 'WARNING'
        elif 500 <= response.status_code <= 599:
            levelname = 'ERROR'

    message = format_response(r)
    log.log(message, level=levelname)



def format_response(r):

    return '{:<10}{:<10}'.format(
        r.status_code,
        r.url
    )


root_logger = logging.getLogger('webspray')
root_logger.setLevel(logging.DEBUG)

### LOG TO STDERR ###

term_handler = logging.StreamHandler()
# tell the handler to use this format
term_handler.setFormatter(ColoredFormatter('%(levelname)s %(message)s'))

### LOG TO FILE ###

logdir = Path(__file__).absolute().parent.parent / 'logs'
logdir.mkdir(parents=True, exist_ok=True)
date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
filename = f'dirspray_{date_str}.log'
log_filename = str(logdir / filename)
log_format = '%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s'
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter(log_format))

root_logger.handlers = [term_handler, file_handler]