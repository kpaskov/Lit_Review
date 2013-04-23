'''
Created on Dec 4, 2012

@author: kpaskov
'''
from model_old_schema.model import get_first
from webapp.litreview_logger import log_it

class MoveRefException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
    
class RefDoesNotExistException(MoveRefException):
    def __init__(self, pubmed_id):
        super(MoveRefException, self).__init__('Reference pubmed_id = ' + pubmed_id + ' has already been linked or discarded.')

def move_reftemp_to_refbad(pubmed_id, session=None):
    """"
    Remove reference from the RefTemp table and add it to the RefBad table.
    """ 
    
    from model_old_schema.reference import RefTemp, RefBad

    def f(session):        
        reftemp = get_first(RefTemp, session, pubmed_id=pubmed_id)
        if reftemp is None:
            raise RefDoesNotExistException(pubmed_id)
        refbad = RefBad.as_unique(session, pubmed_id=pubmed_id)
        
        session.add(refbad)
        session.delete(reftemp)
        return True
    
    return f if session is None else f(session)

            
def move_refbad_to_reftemp(pubmed_id, session=None):
    """"
    Remove reference from the RefBad table and add it to the RefTemp table.
    """     
    
    from model_old_schema.reference import RefTemp, RefBad
    
    def f(session):       
        refbad = get_first(RefBad, session, pubmed_id=pubmed_id)
        if refbad is None:
            raise RefDoesNotExistException(pubmed_id)
        reftemp = RefTemp.as_unique(session, pubmed_id = pubmed_id)
            
        session.add(reftemp)
        session.delete(refbad)
        return True
    
    return f if session is None else f(session)
            
def move_reftemp_to_ref(pubmed_id, session=None):
    """
    Remove reference from the RefTemp table, create a full Reference, and add it to the Reference table.
    """
    
    from model_old_schema.reference import RefTemp, Reference

    def f(session):
        reftemp = get_first(RefTemp, session, pubmed_id=pubmed_id)
        log_it('got_reftemp', 'SUCCESS')
        if reftemp is None:
            raise RefDoesNotExistException(pubmed_id)
        ref = Reference(session, pubmed_id=pubmed_id)
        log_it('created reference', 'SUCCESS')
            
        session.add(ref)
        session.delete(reftemp)
        log_it('adjusted session', 'SUCCESS')

        return True
  
    return f if session is None else f(session)
            
def move_ref_to_reftemp(pubmed_id, session=None):
    """
    Remove reference from the Reference table and add it to the RefTemp table.
    """
    
    from model_old_schema.reference import RefTemp, Reference

    def f(session):        
        ref = get_first(Reference, session, pubmed_id=pubmed_id)
        if ref is None:
            raise RefDoesNotExistException(pubmed_id)
        reftemp = RefTemp.as_unique(session, pubmed_id=pubmed_id)
            
        session.add(reftemp)
        session.delete(ref)
        return True
    
    return f if session is None else f(session)
