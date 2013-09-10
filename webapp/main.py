'''
Created on Feb 1, 2013

@author: kpaskov
'''
from webapp.config import DBTYPE, DBHOST, DBNAME, SECRET_KEY, SCHEMA, HOST, PORT


if __name__ == "__main__":
    
    from webapp.users import setup_users
    setup_users(['maria', 'julie', 'dwight', 'kpaskov', 'fisk', 'rama', 'stacia', 'nash', 'marek', 'otto'])
    
    from model_old_schema.model import Model
    from webapp import router
    router.model = Model(DBTYPE, DBHOST, DBNAME, SCHEMA)
    router.app.secret_key = SECRET_KEY
    router.app.run(host=HOST, port=PORT, debug=True)  