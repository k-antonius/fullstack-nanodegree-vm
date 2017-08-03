'''
Created on Jul 9, 2017

@author: kennethalamantia
'''

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    email = Column(String(80), nullable = False)
    picture = Column(String(80))

class Category(Base):
    __tablename__ = 'category'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    User = relationship(User)
    
    @property
    def serialize(self):
        '''Return copy of object attributes as
        dictionary.
        '''
        return {'name' : self.name,
                'id' : self.id
                }


class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    quantity = Column(Integer)
    price = Column(Integer)
    category_id = Column(Integer, ForeignKey('category.id'))
    Category = relationship(Category)
    
    @property
    def serialize(self):
        return {'name' : self.name,
                'id' : self.id,
                'description' : self.description,
                'quantity' : self.quantity,
                'price' : self.price,
                'category_id' : self.category_id,
                'purchaser' : self.purchaser
                }


### End of file  ###
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)