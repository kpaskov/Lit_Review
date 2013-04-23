'''
Created on Apr 23, 2013

@author: kpaskov
'''
from flask_login import current_user
import logging

def log_it(action, state, variables=None):
    if variables is not None:
        logging.debug('%s %s %s %s', action, state, current_user.name, variables)
    else:
        logging.debug('%s %s %s', action, state, current_user.name)
        
def log_it_info(action, state, variables=None):
    if variables is not None:
        logging.info('%s %s %s %s', action, state, current_user.name, variables)
    else:
        logging.info('%s %s %s', action, state, current_user.name)