import sys
sys.stdout=sys.stderr

from webapp.router import app as application
from model_old_schema.model import Model
from webapp import router

router.model = Model('oracle', 'fasolt.stanford.edu:1521', 'SDEV', 'bud')
application.secret_key = 'my secret key'