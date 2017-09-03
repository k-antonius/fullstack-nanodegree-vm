'''
Created on Jul 9, 2017

@author: kennethalamantia
'''

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# association table
pantry_access = Table('pantry_access', Base.metadata,
                      Column('user_id', Integer, ForeignKey('users.id')),
                      Column('pantry_id', Integer, ForeignKey('pantry.id')))

class User(Base):
    __tablename__ = 'users'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    email = Column(String(80), nullable = False)
    children = relationship('Pantry', secondary=pantry_access, backref='users')
    
    
    def __init__(self, name, email):
        self.name = name
        self.email = email


class Pantry(Base):
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

class ShareRequest(Base):
    '''Table that stores the status of user requests to share pantries.
    '''
    __tablename__ = 'shareRequest'
    id = Column(Integer, primary_key = True)
    sender = Column(Integer, ForeignKey('users.id'))
    recipient = Column(Integer, ForeignKey('users.id'))
    viewed = Column(Boolean(create_constraint=False))
    
    def __init__(self, sender, recipient):
        self.sender = sender
        self.recipient = recipient


def createDB(testing=False):
#     engine = None
    if testing:
        engine = create_engine('sqlite:///test_item_catalog.db')
    else:
        engine = create_engine('sqlite:///item_catalog.db')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)









