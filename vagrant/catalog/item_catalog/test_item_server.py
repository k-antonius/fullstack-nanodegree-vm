'''
Created on Aug 5, 2017

@author: kennethalamantia
'''
import os
import item_server
import unittest
from test_db_populator import User, Category, Pantry, Item, MockDB
from db_API import DBInterface

class TestMockDatabase(unittest.TestCase):
    '''Tests the base functionality of the mock database.
    '''

    def setUp(self):
        self.mDB = MockDB()
        self.db = DBInterface(self.mDB, testing=True)


    def tearDown(self):
        pass


    def testReadMockDB(self):
        
        self.assertEqual(self.db.getDBObjectById('Category', 1).name, 
                         'vegetables')
        self.assertEqual(self.db.getDBObjectByName('Category', 'snacks', 2).name,
                         'snacks')
        self.assertEqual(self.db.getDBObjectByName('Item','apple', 1).name, 
                         'apple')
        # categories in pantry 1
        pantry1Categories = self.db.getAllObjects('Category', 1)
        self.assertListEqual(pantry1Categories, [self.mDB.categories[0],
                                                 self.mDB.categories[1],
                                                 self.mDB.categories[2]])
        # items in pantry 2, category 3
        category3Items = self.db.getAllObjects('Item', 3)
        self.assertListEqual(category3Items, [self.mDB.items[4], 
                                              self.mDB.items[5]])
        # check getting object that does not exist
        self.assertEqual(self.db.getDBObjectById('Category', 17), None)
        self.assertEqual(self.db.getUserByEmail('A@aaa.com').name, 'A')
        
    def testAdd(self):
        '''Test add operations on mock db
        '''
#         new_item = Item(None, 'pear', 'pear-shaped', 1, 1.0, 1)
        self.assertEqual(self.db.getDBObjectById('Item', 8), None)
        self.db.addObject('Item', 'pear', 'pear-shaped', 1, 1.0, 1)
        self.assertEqual(self.db.getDBObjectByName('Item', 'pear', 1).name, 
                         'pear')
        self.assertEqual(self.db.getDBObjectById('Item', 8).id, 8)
        
    def testDelete(self):
        '''Test delete operations on mock db
        '''
        to_delete = self.db.getDBObjectById('Item', 6)
        self.db.delObject(to_delete)
        self.assertEqual(self.db.getDBObjectById('Item', 6), None)
        self.assertEqual(len(self.mDB.items), 6)
        
    # test editing
    def testEdit(self):
        '''test edit operations on mock db
        '''
        to_edit = self.db.getDBObjectById('Category', 6)
        to_edit.name = "meats"
        self.assertTrue(self.db.getDBObjectByName('Category', "meats", 2), 
                        "update to meats failed")

class TestServer(unittest.TestCase):
    def setUp(self):
        item_server.app.testing = True
        self.app = item_server.app.test_client()
        self.mDB = MockDB()
        item_server.mock_database = self.mDB
        
    def tearDown(self):
        item_server.mock_database = None
        
    def testPantryIndex1(self):
        '''Mock user A.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "A@aaa.com"
        r = self.app.get('/pantry/', follow_redirects=True)
        self.assertTrue('Pantry_A' in r.data)
        self.assertTrue('Pantry_B' in r.data)
        self.assertFalse('Pantry_C' in r.data)
        
    def testPantryIndex2(self):
        '''Mock user B.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "B@bbb.com"
        r = self.app.get('/pantry/', follow_redirects=True)
        self.assertTrue('Pantry_C' in r.data)
        self.assertTrue('Pantry_B' in r.data)
        self.assertFalse('Pantry_A' in r.data)
        
    def testPantryIndexNoUser(self):
        '''No User logged in.
        '''
        r = self.app.get('/pantry/', follow_redirects=True)
        self.assertTrue('You must log in to view that page.' in r.data)
    
    def testCategoryIndex(self):
        '''Test the category index page with a user having access.
        '''
        # mock user A has acces to pantry 1
        with self.app.session_transaction() as sess:
            sess['email'] = "A@aaa.com"
        r = self.app.get('/pantry/1/', follow_redirects=True)
        self.assertTrue('vegetables' in r.data)
        self.assertTrue('starches' in r.data)
        self.assertTrue('desserts' in r.data)
        self.assertFalse('meat' in r.data, 'Should not be there.')

    def testCategoryIndexWrongUser(self):
        '''Logged in user does not have access to this cateogry.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "B@bbb.com"
        r = self.app.get('/pantry/1/', follow_redirects=True)
        self.assertTrue('You do not have access to that page.' in r.data)
        
    def testCategoryIndexNoUser(self):
        '''Test the category index page with no logged in user.
        '''
        r = self.app.get('/pantry/1/', follow_redirects=True)
        self.assertTrue('You must log in to view that page.' in r.data)
        
    def testAddCategory(self):
        '''Test adding a category for user C.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'C@ccc.com'
        r = self.app.post('/pantry/3/category/add', data=dict(
            name='new_category'), follow_redirects=True)
        self.assertTrue('new_category' in r.data)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
