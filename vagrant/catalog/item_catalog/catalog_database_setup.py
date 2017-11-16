'''
Created on Jul 9, 2017

@author: kennethalamantia

Module defines the model schema and contains a function for creating the
database when deploying the application.
'''

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# association table mapping users to the pantries they can access - a 
# many-to-many relationship
pantry_access = Table('pantry_access', Base.metadata,
                      Column('user_id', Integer, ForeignKey('users.id')),
                      Column('pantry_id', Integer, ForeignKey('pantry.id')))

class User(Base):
    '''Table holding information about users.
    name - user name, not necessarily unique
    id - unique id for each user
    email - email address from OAuth2 provider
    children - pantries this user can access
    Deleting a user removes the user and all owned pantries from the database.
    '''
    __tablename__ = 'users'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    email = Column(String(80), nullable = False)
    children = relationship('Pantry', secondary=pantry_access, backref='users')
    
    
    def __init__(self, name, email):
        self.name = name
        self.email = email


class Pantry(Base):
    '''Table holding information about pantries.
    name - name of pantry, not necessarily unique
    id - unique pantry id
    parent_id - user owner of this pantry (only one user owns this pantry)
    children - the categories associated with this pantry (one to many)
    Deleting a pantry removes the pantry and all children.
    '''
    __tablename__ = 'pantry'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    parent_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    children = relationship('Category', backref='parent',
                              cascade='all, delete-orphan')
    
    def __init__(self, name, parent_id):
        self.name = name
        self.parent_id = parent_id
    
    @property
    def serialize(self):
        '''Return object attributes as dict
        '''
        return {'name' : self.name,
                'id' : self.id,
                'parent_id' : self.parent_id}


class Category(Base):
    '''Table contains information about categories witin pantries.
    name - name of the category, not unique
    id - unique id of category
    parent_id - the pantry to which this category belongs
    children - the list of items in this category
    '''
    __tablename__ = 'category'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    parent_id = Column(Integer, ForeignKey('pantry.id'), nullable=False)
    children = relationship('Item', backref = 'parent',
                         cascade='all, delete-orphan')
    
    def __init__(self, name, parent_id):
        self.name = name
        self.parent_id = parent_id
    
    @property
    def serialize(self):
        '''Return copy of object attributes as
        dictionary.
        '''
        return {'name' : self.name,
                'id' : self.id,
                'parent_id' : self.parent_id
                }


class Item(Base):
    '''Table containing information about items.
    name - name of the item
    id - unique id of the item
    description - short description of the itme
    quantity - number of the item
    price - cost to purchase this item
    parent_id - id of the category to which this item belongs
    '''
    __tablename__ = 'item'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    quantity = Column(Integer)
    price = Column(Integer)
    parent_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    
    def __init__(self, name, description, quantity, price, parent_id):
        self.name = name
        self.description = description
        self.quantity = quantity
        self.price = price
        self.parent_id = parent_id
    
    @property
    def serialize(self):
        return {'name' : self.name,
                'id' : self.id,
                'description' : self.description,
                'quantity' : self.quantity,
                'price' : self.price,
                'parent_id' : self.parent_id,
                'purchaser' : self.purchaser
                }


def create_db(testing=False):
    '''Create a production or test database. Run this function from the console
    when deploying the application before running item_server for the first
    time.
    '''
    if testing:
        engine = create_engine('sqlite:///test_item_catalog.db')
    else:
        engine = create_engine('postgresql://catalog:what a drag@localhost/catalog')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)









