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
from item_catalog.catalog_database_setup import Base, Category, Item, Pantry, \
                                                User

class DBInterface(object):
    '''This class acts as an interface to either an actual database for 
    production or live testing, or a testing version that uses normal
    in memory python data structures. 
    '''
    @classmethod
    def make_session_factory(cls, testing=False):
        '''Create a SQL Alchemy session factory. This is not used in the 
        initializer because there is no need to re-create the factory object
        every time an instance of this class is created.
        '''
        if testing:
            engine = create_engine('sqlite:///test_item_catalog.db')
        else:
            engine = create_engine('postgresql://catalog:what a drag@localhost/catalog')
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

    def get_db_object_by_id(self, obj_class, obj_id):
        '''Get single database object based on its ID.
        @param obj_class: string class name of the model
        @param obj_id: int id of the model
        '''
        return self.db.get_obj(obj_class, obj_id)

    def get_all_objects(self, obj_class, parent_id):
        '''Get all objets of given class. If superID is supplied,
        only objects directly related to superId will be returned.
        @param obj_class: string class name of the model
        @param parent_id: int id of the parent 
        '''
        return self.db.get_all_objects(obj_class, parent_id)

    def get_dbobject_by_name(self, obj_class, name, parent_id):
        '''Return any objects matching this query as a list.
        @param obj_class: the Mapped class
        @param name: string name of this object
        @param parent_id: the id of this object's pantry 
        '''
        return self.db.get_obj_by_name(obj_class, name, parent_id)

    def get_user_by_email(self, email):
        '''Return the user matching the email address if any.
        @param email: an email address as a string
        '''
        return self.db.get_user_by_email(email)

    def get_authorized_pantries(self, user):
        '''Return a list of users authorized to access a pantry
        @param user: the accessing user ORM object.
        '''
        return self.db.get_authorized_pantries(user)

    def add_object(self, class_name, *args):
        '''Add an object to the database. 
        @param class_name: the name of the class the new object is to be
        an instance of
        @param args: values to populate the fields of the model class
        '''
        self.db.add_object(class_name, *args)


    def del_object(self, obj):
        '''CRUD delete this entity from the database.
        @param obj: the object to be deleted
        '''
        self.db.del_object(obj)

    def update_object(self, obj):
        '''CRUD update on this database entity.
        @param obj: the object to be deleted
        '''
        self.db.update_object(obj)


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

    def get_user_by_email(self, email):
        '''Get user object by email address.
        @param email: string email address
        @return: the user model object or None if not found
        '''
        try:
            return filter(lambda x: x.email == email,
                          self.session.mock_db.get("User"))[0]
        except IndexError:
            return None

    def get_obj(self, obj_class, obj_id):
        '''Get a model object by class name and id.
        @param obj_class: string name of the model
        @param obj_id: the int id of the model object
        @return: model object instance or None if not found
        '''
        try:
            return filter(lambda x: x.id == obj_id,
                          self.session.mock_db.get(obj_class))[0]
        except IndexError:
            return None


    def get_obj_by_name(self, obj_class, obj_name, obj_parent_id):
        '''Get a model object by its name field.
        @param obj_class: model class name
        @param obj_name: name of individual model object
        @param obj_parent_id: int id of the parent
        @return: model object instance or None if not found
        '''
        try:
            return filter(lambda x: x.name == obj_name and x.parent_id\
                           == obj_parent_id,
                          self.session.mock_db.get(obj_class))[0]
        except IndexError:
            return None

    def get_all_objects(self, obj_class, parent_id):
        '''Returns a list of all object of a specific mapped class in
        the table with a given parent relationship.
        @param obj_class: model class name
        @param parent_id: int id of the parent
        '''
        return filter(lambda x: x.parent_id == parent_id,
                      self.session.mock_db.get(obj_class))

    def get_authorized_pantries(self, user):
        '''Return a list of pantry objects this user can access.
        @param user: the user to check.
        '''
        return filter(lambda x: x.id in user.pantries, self.session.pantries)

    def add_object(self, class_name, *args):
        '''Add an object to the database. 
        @param class_name: the name of the class the new object is to be
        an instance of
        @param args: values to populate the fields of the model class
        '''
        mock_table = self.session.mock_db.get(class_name)
        # get the constructor from the mock database --
        # the construtors are in a dict, would conflict with names of
        # mapped classes for ORM
        constructor = self.session.constructor.get(class_name)
        # make a new id for the object, assume it is going at the end of the
        # list (mock db lists are ordered by id)
        new_id = mock_table[len(mock_table) - 1].id + 1
        args_with_id = list(args)
        args_with_id.insert(0, new_id)
        new_obj = constructor(*args_with_id)
        new_obj.id = new_id
        mock_table.append(new_obj)
        # if it is a pantry need to update user pantry access id reference
        if class_name == 'Pantry':
            user = filter(lambda x:x.id == new_obj.parent_id,
                          self.session.mock_db.get('User'))
            user[0].pantries.append(new_obj.id)

    def del_object(self, obj):
        '''Delete an object from the mock database.
        @param obj: model object to delete
        '''
        mock_table = self.session.mock_db.get(obj.__class__.__name__)
        mock_table.remove(obj)


    def update_object(self, obj):
        '''Update an existing entry in the mock table. Does not actually 
        do anything because the object's properties will already be updated
        in the handler. Throws an exception if the object is not in the 
        list.
        '''
        mock_table = self.session.mock_db.get(obj.__class__.__name__)
        assert obj in mock_table

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

    def get_obj(self, obj_class_name, obj_id):
        '''Returns an ORM object. Raise an exception if more than one is found.
        @param obj_class_name: ORM table class, as a string
        @param obj_id: integer id of the object to query for
        '''
        obj_class = self.classes[obj_class_name]
        return self.session.query(obj_class).\
            filter_by(id=obj_id).one()

    def get_all_objects(self, obj_class_name, parent_id):
        '''Returns a list of all cateogies as ORM objects.
        @param session: SQL Alchemy session instance.
        '''
        obj_class = self.classes[obj_class_name]
        return self.session.query(obj_class).filter_by(parent_id=parent_id).\
               order_by(obj_class.id).all()

    def get_obj_by_name(self, obj_class_name, name, parent_id):
        '''Get the object with a given name associated with a specific parent.
        Returns None if no object with that name is found.
        '''
        obj_class = self.classes[obj_class_name]
        return self.session.query(obj_class).filter(\
                                    and_(obj_class.name == name,
                                         obj_class.parent_id == parent_id))\
                                         .first()

    def get_user_by_email(self, email):
        '''Get a user by their email address, will return None if no user is
        found.
        '''
        return self.session.query(User).filter_by(email=email).first()

    def get_authorized_pantries(self, user):
        '''Return a list of the pantries this user has access to,
        sorted by pantry id.
        @param user: an instance of the mapped user object
        '''
        return sorted(user.children, key=lambda pantry: pantry.id)

    def add_object(self, class_name, *args):
        '''Add an object to the database.
        @param obj: the object to add
        @param args: data for the columns of mapped class
        '''
        obj = self.classes[class_name](*args)
        if class_name in self.parents:
            parent_class = self.classes[self.parents[class_name]]
            parent = self.session.query(parent_class)\
                     .filter_by(id=obj.parent_id).one()
            parent.children.append(obj)
        self.session.add(obj)

    def del_object(self, obj):
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
