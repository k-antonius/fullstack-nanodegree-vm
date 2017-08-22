'''
Created on Aug 7, 2017

@author: kennethalamantia
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, Category, Item, Pantry, User

class DBInterface(object):
    '''This class acts as an interface to either an actual database for 
    production or live testing, or a testing version that uses normal
    in memory python data structures. 
    '''
    @classmethod
    def makeSessionFactory(cls):
        '''Create a SQL Alchemy session factory. This is not used in the 
        initializer because there is no need to re-create the factory object
        every time an instance of this class is created.
        '''
        engine = create_engine('sqlite:///item_catalog.db')
        Base.metadata.bind = engine
        return sessionmaker(bind=engine)
    
    def __init__(self, session, testing=False):
        '''If testing is true, will use the mock database implementation, 
        otherwise uses SQL Alchemy queries. 
        @param session: an SQL alchemy session for running a real database, 
        for testing session is an instance of MockDB from the test_db_populator
        class. 
        '''
        self.testing = testing
        if self.testing:
            self.db = MockDBAccessor(session)
        else:
            self.db = DBAccessor(session)
    
    def getDBObjectById(self, objClass, objId):
        '''Get single database object based on its ID.
        '''
        return self.db.getObj(objClass, objId)
    
    def getAllObjects(self, objClass, superId):
        '''Get all objets of given class. If superID is supplied,
        only objects directly related to superId will be returned.
        '''
        return self.db.getAllObjects(objClass, superId)
    
    def getDBObjectByName(self, objClass, name, parentId):
        '''Return any objects matching this query as a list.
        @param objClass: the Mapped class
        @param name: string name of this object
        @param parentId: the id of this object's pantry 
        '''
        return self.db.getObjByName(objClass, name, parentId)
    
    def getUserByEmail(self, email):
        '''Return the user matching the email address if any.
        @param email: an email address as a string
        '''
        return self.db.getUserByEmail(email)
    
    def getAuthorizedPantries(self, user):
        '''Return a list of users authorized to access a pantry
        @param user: the accessing user.
        '''
        if self.testing:
            return self.db.getAuthorizedPantries(user)
    
    def addObject(self, className, *args):
        '''Add an object to the database. 
        @param className: the name of the class the new object is to be
        an instance of
        @param kwargs: keys are the fields of the class and values are the
        data
        '''
        if self.testing:
            self.db.addObject(className, *args)
        else:
            pass
        
    def delObject(self, obj):
        '''CRUD delete this entity from the database.
        '''
        self.db.delObject(obj) 
        
    def updateObject(self, obj):
        '''CRUD update on this database entity.
        '''
        self.db.updateObject(obj)


class MockDBAccessor(object):
    def __init__(self, session):
        self.session = session
    
    def getUserByEmail(self, email):
        try:
            return filter(lambda x: x.email == email, 
                          self.session.mock_db.get("User"))[0]
        except IndexError:
            return None
        
    def getObj(self, objClass, objId):
        try:
            return filter(lambda x: x.id == objId,
                          self.session.mock_db.get(objClass))[0]
        except IndexError:
            return None
            
                          
    def getObjByName(self, objClass, objName, objParentId):
        try:
            return filter(lambda x: x.name == objName and x.parent_id == objParentId,
                          self.session.mock_db.get(objClass))[0]
        except IndexError:
            return None
    
    def getAllObjects(self, objClass, parentId):
        '''Returns a list of all object of a specific mapped class in
        the table with a given parent relationship.
        '''
        return filter(lambda x: x.parent_id == parentId, 
                      self.session.mock_db.get(objClass))
        
    def getAuthorizedPantries(self, user):
        '''Return a list of pantry objects this user can access.
        @param user: the user to check.
        '''
        return filter(lambda x: x.id in user.pantries, self.session.pantries)
        
    def addObject(self, className, *args):
        '''Create a new entry in the mock table. 
        '''
        mockTable = self.session.mock_db.get(className)
        constructor = self.session.constructor.get(className)
        new_id = mockTable[len(mockTable)-1].id + 1
        argsWithId = list(args)
        argsWithId.insert(0, new_id)
        newObj = constructor(*argsWithId)
        newObj.id = new_id
        mockTable.append(newObj)
        # if it is a pantry need to update user pantry access id reference
        if className == 'Pantry':
            user = filter(lambda x:x.id == newObj.parent_id,
                          self.session.mock_db.get('User'))
            user[0].pantries.append(newObj.id)
    
    def delObject(self, obj):
        '''Delete an object from the list.
        '''
        mockTable = self.session.mock_db.get(obj.__class__.__name__)
        mockTable.remove(obj)
        
        
    def updateObject(self, obj):
        '''Update an existing entry in the mock table. Does not actually 
        do anything because the object's properties will already be updated
        in the handler. Throws an exception if the object is not in the 
        list.
        '''
        mockTable = self.session.mock_db.get(obj.__class__.__name__)
        assert obj in mockTable

class DBAccessor(object):
    '''Provides access to the database as necessary.
    Serves as a mid-layer between the ORM and view functions. 
    ''' 
     
    def __init__(self, session):
        self.session = session
        self.classes = {'User' : User,
                        'Pantry' : Pantry,
                        'Category' : Category,
                        'Item' : Item}
      
    def getDBObj(self, objClass, objID):
        '''Returns an ORM object.
        @param session: SQLAlchemy session instance
        @param objClass: ORM table class
        @param objID: ORM row object
        '''
        return self.session.query(objClass).filter_by(id=objID).one()
        
              
    def getObjByName(self, objClass, name, parentId):
        '''No exception is thrown if this fails.
        '''
        return self.session.query(objClass).filter_by(name=name).first()
      
    def getAllObjects(self, objClass, parentId):
        '''Returns a list of all cateogies as ORM objects.
        @param session: SQL Alchemy session instance.
        '''
        return self.session.query(objClass).filter_by(parent_id=parentId).\
               order_by(objClass.name).all()
            
    def getUser(self):
        pass
    
    def adduser(self):
        pass