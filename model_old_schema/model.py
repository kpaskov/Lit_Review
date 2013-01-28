'''
Created on Oct 18, 2012

@author: kpaskov

This class is used to perform queries and operations on the corresponding database. In this case, the BUD schema on fasolt.

'''
from model_old_schema import Base
from model_old_schema.config import DBTYPE, DBHOST, DBNAME
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker


# imports of model classes from model.feature, model.taxonomy, etc are done as needed, since these imports are
# not available until AFTER the metadata is bound to the engine.  

class DBConnectionLostException(Exception):
    def __init__(self):
        self.message = "The connection to the database has been lost. Please try logging in again."
    def __str__(self):
        return repr(self.message)

class Model(object):
    '''
    This class acts as a divider between the Oracle back-end and the application. In order to pull information
    from the Oracle DB, this class MUST be called.
    '''
    engine = None
    SessionFactory = None
 
    def connect(self, username, password):
        """
        Create engine, associate metadata with the engine, then create a SessionFactory for use through the backend.
        """
        self.engine = create_engine("%s://%s:%s@%s/%s" % (DBTYPE, username, password, DBHOST, DBNAME), convert_unicode=True, pool_recycle=3600)
        Base.metadata.bind = self.engine
        self.SessionFactory = sessionmaker(bind=self.engine)

        return
    
    def is_connected(self):
        #Checks if a connection to the db has been made.
        try:
            self.engine.connect()
            return True
        except:                 
            return False
        
    def execute(self, f, username, commit=False, **kwargs):
        if not self.is_connected():
            raise DBConnectionLostException()
        try:
            session = self.SessionFactory()
            session.user = username.upper()
            response = f(session, **kwargs)
            if commit:
                session.commit()
            return response
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

def get(model, session=None, **kwargs):
    def f(session):
        return session.query(model).filter_by(**kwargs).all()
    
    return f if session is None else f(session)
    
def get_first(model, session=None, **kwargs):
    def f(session):
        return session.query(model).filter_by(**kwargs).first()
    
    return f if session is None else f(session)

def count(model, session=None, **kwargs):
    def f(session):
        return session.query(model).filter_by(**kwargs).count()
    
    return f if session is None else f(session)

    
    