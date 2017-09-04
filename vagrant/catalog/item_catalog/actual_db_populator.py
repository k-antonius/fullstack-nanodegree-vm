'''
Created on Aug 26, 2017

@author: kennethalamantia

This module contains information to populate the test database.
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, User, Pantry, Category, Item, create_db

class MockDB(object):

    def __init__(self):
        '''Creates entities to populate the mock database.
        '''
        self.mock_users = (User('A', 'A@aaa.com'),
                           User('B', 'B@bbb.com'),
                           User('C', 'C@ccc.com'))
        
        self.pantries = [Pantry('Pantry_A', 1),
                         Pantry('Pantry_B', 2),
                         Pantry('Pantry_C', 3),
                         Pantry('Pantry_D', 1)]
        
        self.categories = [Category('vegetables', 1),
                           Category('starches', 1),
                           Category('desserts', 1),
                           Category('veggies', 2),
                           Category('snacks', 2),
                           Category('meat', 2),
                           Category('fruit', 3), # 7
                           Category('meat', 3),
                           Category('drinks', 3)]
        
        self.items = [Item('apple', 'shiny and red', 5, 1, 1),  # 0
                      Item('broccoli', 'small tree', 10, 5, 1), # 1
                      Item('chips', 'crispy', 4, 5, 5),         # 2
                      Item('steak', 'high in protein', 1, 20, 8),
                      Item('seltzer', 'fizzy', 15, 1, 3),
                      Item('cake', 'moist', 1, 15, 3),
                      Item('potato', 'high in carbs', 50, 20, 2),
                      Item('apple', 'shiny and red', 5, 1, 7)]
        
    def populate(self):
        '''Use this method to create and populate an SQLite database with the 
        information contained in this class.
        '''
        create_db(testing=True)
        engine = create_engine('sqlite:///test_item_catalog.db')
        Base.metadata.bind = engine
        session_maker = sessionmaker(bind=engine)
        session = session_maker()
        entities = [self.mock_users, self.pantries, self.categories,
                    self.items]
        for entity_type in entities:
            for concrete_entity in entity_type:
                if type(concrete_entity) is Pantry:
                    user = session.query(User).\
                    filter_by(id=concrete_entity.parent_id).one()
                    user.children.append(concrete_entity)
                session.add(concrete_entity)
                session.commit()
                
        # Pantry B is shared with user A
        pantryB = session.query(Pantry).filter_by(id=2).one()
        userA = session.query(User).filter_by(id=1).one()
        userA.children.append(pantryB)
        session.commit()
        session.close()        
        