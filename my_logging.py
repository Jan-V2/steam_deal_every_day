import datetime


# this file is called my_logging instead of logging because it causes bugs

from platfowm_vars import ROOTDIR, dir_sep


# todo make this use json and make a gui tool for filtering and viewing logfiles


def log_warning(logline):
    log(logline, 'Warning')

def log_error(logline):
    log(logline, 'ERROR')

def log_message(logline):
    log(logline, 'Message')

def log_exept(logline): # does this perform same function as log_error?
    log(logline, 'Exept')

def log_return():# puts an empty line in the logfile
    write_to_logfile('')

def log(logline, log_type):
    write_to_logfile(log_type + ': ' + get_timestamp() + " " + logline)

def write_to_logfile(line):
    print(line)
    with open(ROOTDIR + dir_sep + "log.txt",mode='a') as logfile:
        logfile.write(line + '\n')

def get_timestamp():
    return '[{:%Y-%m-%d_%H-%M-%S}]'.format(datetime.datetime.now())
