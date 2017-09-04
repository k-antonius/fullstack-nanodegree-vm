'''
Created on Aug 7, 2017
@author: kennethalamantia

This module contains three classes DBInterface, MockDBAccessor, and DBAccessor.
DBInterface is the interface that the application uses to make database calls,
allowing a complete separation of concerns between the application code and 
database code.
DBInterface makes call using the MockDBAccessor class when the testing flag
is true. This allows the appication to be tested independently from a database.
DBInterface useses DBAccessor to access a live database using SQLAlchemy.

The structure of the scheme is based on the following parent-->child
relationship: User-->Pantry(owned, not shared)-->Category-->Item. In the
docstrings below, references to parent are to a direct parent and child to a 
direct child.
'''

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, Category, Item, Pantry, User

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
        module. 
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
        self.db.session.close()
    
    def getDBObjectById(self, objClass, objId):
        '''Get single database object based on its ID.
        @param objClass: string class name of the model
        @param objId: int id of the model
        '''
        return self.db.getObj(objClass, objId)
    
    def getAllObjects(self, objClass, parentId):
        '''Get all objets of given class. If superID is supplied,
        only objects directly related to superId will be returned.
        @param objClass: string class name of the model
        @param parentId: int id of the parent 
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
        @param args: values to populate the fields of the model class
        '''
        self.db.addObject(className, *args)
        
        
    def delObject(self, obj):
        '''CRUD delete this entity from the database.
        @param obj: the object to be deleted
        '''
        self.db.delObject(obj) 
        
    def updateObject(self, obj):
        '''CRUD update on this database entity.
        @param obj: the object to be deleted
        '''
        self.db.updateObject(obj)


class MockDBAccessor(object):
    '''This class accesses the mock database implemented in the 
    test_db_populator module, allowing use of the application in a tightly
    controlled environment without concern to the particular database
    implementation. Notably, this implementation is intended to test the 
    application logic and not perfectly model a database in terms of
    consistency etc.  Refer to the individual functions below in conjunction
    with the test_db_populator module to determine specific behaviour.
     
    When instanting this class, an instance of the
    MockDB class must be passed as the session parameter of the constructor.
    A different mock database could be used, provided the interface was the 
    same.
    '''
    def __init__(self, session):
        '''Instantiate a new mock db test class. This class should only be
        instantiated in the DBInterface class.
        @param session: an instance of MockDB from test_db_populator
        '''
        self.session = session
    
    def getUserByEmail(self, email):
        '''Get user object by email address.
        @param email: string email address
        @return: the user model object or None if not found
        '''
        try:
            return filter(lambda x: x.email == email, 
                          self.session.mock_db.get("User"))[0]
        except IndexError:
            return None
        
    def getObj(self, objClass, objId):
        '''Get a model object by class name and id.
        @param objClass: string name of the model
        @param objId: the int id of the model object
        @return: model object instance or None if not found
        '''
        try:
            return filter(lambda x: x.id == objId,
                          self.session.mock_db.get(objClass))[0]
        except IndexError:
            return None
            
                          
    def getObjByName(self, objClass, objName, objParentId):
        '''Get a model object by its name field.
        @param objClass: model class name
        @param objName: name of individual model object
        @param objParentId: int id of the parent
        @return: model object instance or None if not found
        '''
        try:
            return filter(lambda x: x.name == objName and x.parent_id\
                           == objParentId,
                          self.session.mock_db.get(objClass))[0]
        except IndexError:
            return None
    
    def getAllObjects(self, objClass, parentId):
        '''Returns a list of all object of a specific mapped class in
        the table with a given parent relationship.
        @param objClass: model class name
        @param parentId: int id of the parent
        '''
        return filter(lambda x: x.parent_id == parentId, 
                      self.session.mock_db.get(objClass))
        
    def getAuthorizedPantries(self, user):
        '''Return a list of pantry objects this user can access.
        @param user: the user to check.
        '''
        return filter(lambda x: x.id in user.pantries, self.session.pantries)
        
    def addObject(self, className, *args):
        '''Add an object to the database. 
        @param className: the name of the class the new object is to be
        an instance of
        @param args: values to populate the fields of the model class
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
        '''Delete an object from the mock database.
        @param obj: model object to delete
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
    Serves as a mid-layer between the ORM and view functions. See module and
    DBInterface documentation for more details. This class should only be 
    instantiated in the DBInterface class. 
    ''' 
     
    def __init__(self, session):
        '''Should only be called in DBInterface class.
        @param session: SQLAlchemy session instance.
        @field classes: model class names, used to look up constructor
        @field parents: mapping of child to parent, used to determine type of
        parent knowing model class of child when adding a child in a many-one
        relationship 
        '''
        self.session = session
        # access to constructor from string
        self.classes = {'User' : User,
                        'Pantry' : Pantry,
                        'Category' : Category,
                        'Item' : Item}
        # table allows retrieval of parent from only knowing child 
        self.parents = {'Item' : 'Category',
                        'Category' : 'Pantry',
                        'Pantry' : 'User'}
      
    def getObj(self, objClassName, objId):
        '''Returns an ORM object. Raise an exception if more than one is found.
        @param objClassName: ORM table class, as a string
        @param objId: integer id of the object to query for
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
    
    
    
    
    
    