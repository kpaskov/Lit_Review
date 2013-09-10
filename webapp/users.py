'''
Created on Jan 17, 2013

@author: kpaskov
'''
from flask_login import UserMixin, AnonymousUser
import datetime

USERS = None
USER_NAMES = None

class User(UserMixin):
    def __init__(self, name, user_id, active=True):
        self.name = name
        self.id = user_id
        self.active = active
        self.logged_in = False
        self.last_alive = None

    def is_active(self):
        return self.active
    
    def login(self):
        self.logged_in = True
        self.alive()
        
    def alive(self):
        self.last_alive = datetime.datetime.now()
        
    def logout(self):
        self.logged_in = False
        self.last_alive = None
        
    def is_alive(self):
        return self.logged_in and datetime.datetime.now() - self.last_alive < datetime.timedelta(hours=2)
    
    def __repr__(self):
        data = self.id, self.name, self.active
        return 'User(id=%s, name=%s)' % data

class Anonymous(AnonymousUser):
    name = u"Anonymous"
    def alive(self):
        pass

def setup_users(usernames):
    keys = range(0, len(usernames))
    values = map(lambda (i, username): User(username, i), enumerate(usernames))

    global USERS
    global USER_NAMES
    
    USERS = dict(zip(keys, values))
    USERS[len(usernames)+1] = User('guest', len(usernames)+1, False)

    USER_NAMES = dict((u.name, u) for u in USERS.itervalues())
