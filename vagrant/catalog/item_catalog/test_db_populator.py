'''
Created on Aug 5, 2017

@author: kennethalamantia
'''

class User(object):
    def __init__(self, id, name, email, picture, pantries):
        self.id = id
        self.name = name
        self.email = email
        self.picture = picture
        self.pantries = pantries
        
    def __repr__(self):
        return self.name
        
class Pantry(object):
    def __init__(self, id, name, parent_id):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        
    def __repr__(self):
        return self.name

    @property
    def serialize(self):
        '''Return object attributes as dict
        '''
        return {'name' : self.name,
                'id' : self.id,
                'parent_id' : self.parent_id}
        
class Category(object):
    def __init__(self, id, name, parent_id):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        
    def __repr__(self):
        return self.name
    
    @property
    def serialize(self):
        '''Return copy of object attributes as
        dictionary.
        '''
        return {'name' : self.name,
                'id' : self.id,
                'parent_id' : self.parent_id
                }

class Item(object):
    def __init__(self, id, name, description, quantity, price, category_id):
        self.id = id
        self.name = name
        self.description = description,
        self.quantity = quantity
        self.price = price
        self.parent_id = category_id
    
    def __repr__(self):
        return self.name
    
    @property
    def serialize(self):
        return {'name' : self.name,
                'id' : self.id,
                'description' : self.description,
                'quantity' : self.quantity,
                'price' : self.price,
                'parent_id' : self.parent_id,
                }
        
class ShareRequest(object):
    def __init__(self, id, sender, recipient, viewed=False):
        self.id = id
        self.sender = sender
        self.recipient = recipient
        self.viewed = viewed
    
    def __repr__(self):
        return self.sender + "-->" + self.recipient

class MockDB(object):

    def __init__(self):
        '''Creates entities to populate the mock database.
        '''
        self.mock_users = (User(1, 'A', 'A@aaa.com', 'A_picture', [1,2,4]),
                           User(2, 'B', 'B@bbb.com', 'B_pic', [2,3]),
                           User(3, 'C', 'C@ccc.com', 'C_pic', [3]))
        
        self.pantries = [Pantry(1, 'Pantry_A', 1),
                         Pantry(2, 'Pantry_B', 2),
                         Pantry(3, 'Pantry_C', 3),
                         Pantry(4, 'Pantry_D', 1)]
        
        self.categories = [Category(1, 'vegetables', 1),
                           Category(2, 'starches', 1),
                           Category(3, 'desserts', 1),
                           Category(4, 'veggies', 2),
                           Category(5, 'snacks', 2),
                           Category(6, 'meat', 2),
                           Category(7, 'fruit', 3),
                           Category(8, 'meat', 3),
                           Category(9, 'drinks', 3)]
        
        self.items = [Item(1, 'apple', 'shiny and red', 5, 1.0, 1),  # 0
                      Item(2, 'broccoli', 'small tree', 10, 0.5, 1), # 1
                      Item(3, 'chips', 'crispy', 4, 5.0, 5),         # 2
                      Item(4, 'steak', 'high in protein', 1, 20.0, 8),
                      Item(5, 'seltzer', 'fizzy', 15, 1.0, 3),
                      Item(6, 'cake', 'moist', 1, 15.0, 3),
                      Item(7, 'potato', 'high in carbs', 50, 0.20, 2)]
        
        self.share_request = []
        
        self.mock_db = {'User' : self.mock_users,
                        'Pantry' : self.pantries,
                        'Category' : self.categories,
                        'Item' : self.items,
                        'ShareRequest' : self.share_request}
        
        self.constructor = {'User' : User,
                            'Pantry' : Pantry,
                            'Category' : Category,
                            'Item' : Item,
                            'ShareRequest' : ShareRequest}
