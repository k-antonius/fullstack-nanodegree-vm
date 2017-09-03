'''
Created on Aug 7, 2017

@author: kennethalamantia
'''

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, Category, Item, Pantry, User, \
                            ShareRequest

class DBInterface(object):
    '''This class acts as an interface to either an actual database for 
    production or live testing, or a testing version that uses normal
    in memory python data structures. 
    '''
    @classmethod
    def makeSessionFactory(cls, testing=False):
        '''Create a SQL Alchemy session factory. This is not used in the 
        initializer because there is no need to re-create the factory object
        every time an instance of this class is created.
        '''
        if testing:
            engine = create_engine('sqlite:///test_item_catalog.db')
        else:
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
            
    def _commit(self):
        '''For testing only. Commits changes to the database.
        '''
        self.db.session.commit()
        
    def _close(self):
        '''For testing only. Closes the session.
        '''
    
    def getDBObjectById(self, objClass, objId):
        '''Get single database object based on its ID.
        '''
        return self.db.getObj(objClass, objId)
    
    def getAllObjects(self, objClass, parentId):
        '''Get all objets of given class. If superID is supplied,
        only objects directly related to superId will be returned.
        '''
        return self.db.getAllObjects(objClass, parentId)
    
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
        @param user: the accessing user ORM object.
        '''
        return self.db.getAuthorizedPantries(user)
    
    def addObject(self, className, *args):
        '''Add an object to the database. 
        @param className: the name of the class the new object is to be
        an instance of
        @param kwargs: keys are the fields of the class and values are the
        data
        '''
        self.db.addObject(className, *args)
        
        
    def delObject(self, obj):
        '''CRUD delete this entity from the database.
        '''
        self.db.delObject(obj) 
        
    def updateObject(self, obj):
        '''CRUD update on this database entity.
        '''
        self.db.updateObject(obj)
        
    def getSharesSent(self, user):
        '''Get the shares this user has sent.
        @param user: the user ORM object
        '''
        pass
    
    def getSharesReceived(self, user):
        '''Get the shares this user has received.
        @param user: the user ORM object
        '''
        pass


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
            return filter(lambda x: x.name == objName and x.parent_id\
                           == objParentId,
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
        # get the constructor from the mock database --
        # the construtors are in a dict, would conflict with names of
        # mapped classes for ORM
        constructor = self.session.constructor.get(className)
        # make a new id for the object, assume it is going at the end of the 
        # list (mock db lists are ordered by id)
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
        # access to constructor from string
        self.classes = {'User' : User,
                        'Pantry' : Pantry,
                        'Category' : Category,
                        'Item' : Item,
                        'ShareRequest' : ShareRequest}
        # table allows retrieval of parent from only knowing child 
        self.parents = {'Item' : 'Category',
                        'Category' : 'Pantry',
                        'Pantry' : 'User'}
      
    def getObj(self, objClassName, objId):
        '''Returns an ORM object. Raise an exception if more than one is found.
        @param objClass: ORM table class, as a string
        @param objID: integer id of the object to query for
        '''
        objClass = self.classes[objClassName]
        return self.session.query(objClass).\
            filter_by(id=objId).one()
      
    def getAllObjects(self, objClassName, parentId):
        '''Returns a list of all cateogies as ORM objects.
        @param session: SQL Alchemy session instance.
        '''
        objClass = self.classes[objClassName]
        return self.session.query(objClass).filter_by(parent_id=parentId).\
               order_by(objClass.id).all()
               
    def getObjByName(self, objClassName, name, parentId):
        '''Get the object with a given name associated with a specific parent.
        Returns None if no object with that name is found.
        '''
        objClass = self.classes[objClassName]
        return self.session.query(objClass).filter(\
                                    and_(objClass.name == name, 
                                         objClass.parent_id == parentId))\
                                         .first()
            
    def getUserByEmail(self, email):
        '''Get a user by their email address, will return None if no user is
        found.
        '''
        return self.session.query(User).filter_by(email=email).first()
    
    def getAuthorizedPantries(self, user):
        '''Return a list of the pantries this user has access to,
        sorted by pantry id.
        @param user: an instance of the mapped user object
        '''
        return sorted(user.children, key=lambda pantry: pantry.id)
    
    def addObject(self, className, *args):
        '''Add an object to the database.
        @param obj: the object to add
        @param args: data for the columns of mapped class
        '''
        obj = self.classes[className](*args)
        if className in self.parents:
            parentClass = self.classes[self.parents[className]]
            parent = self.session.query(parentClass)\
                     .filter_by(id=obj.parent_id).one()
            parent.children.append(obj)
        self.session.add(obj)
        
    def delObject(self, obj):
        '''Delete this object from the database and cascade to all children.
        '''
        self.session.delete(obj)
        # relationship user---pantry is many to many so get owned pantries
        # and delete them
        if type(obj) is User:
            child_pantries = filter(lambda pantry: pantry.parent_id == obj.id,
                                    obj.children)
            assert child_pantries is not None, "No child pantries found"
            for child_pantry in child_pantries:
                self.session.delete(child_pantry)
    
    
    
    
    
    