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
        
    def setGetRequest(self, uri):
        return self.app.get(uri, follow_redirects=True)
    
    def setPostRequest(self, uri, **kwargs):
        return self.app.post(uri, data=kwargs, follow_redirects=True)
        
    def testPantryIndex1(self):
        '''Mock user A.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "A@aaa.com"
        r = self.setGetRequest('/pantry/')
        self.assertTrue('Pantry_A' in r.data)
        self.assertTrue('Pantry_B' in r.data)
        self.assertFalse('Pantry_C' in r.data)
        
    def testPantryIndex2(self):
        '''Mock user B.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "B@bbb.com"
        r = self.setGetRequest('/pantry/')
        self.assertTrue('Pantry_C' in r.data)
        self.assertTrue('Pantry_B' in r.data)
        self.assertFalse('Pantry_A' in r.data)
        
    def testPantryIndexNoUser(self):
        '''No User logged in.
        '''
        r = self.setGetRequest('/pantry/')
        self.assertTrue('You must log in to view that page.' in r.data)
    
    def testCategoryIndex(self):
        '''Test the category index page with a user having access.
        '''
        # mock user A has acces to pantry 1
        with self.app.session_transaction() as sess:
            sess['email'] = "A@aaa.com"
        r = self.setGetRequest('/pantry/1/')
        self.assertTrue('vegetables' in r.data)
        self.assertTrue('starches' in r.data)
        self.assertTrue('desserts' in r.data)
        self.assertFalse('meat' in r.data, 'Should not be there.')

    def testCategoryIndexWrongUser(self):
        '''Logged in user does not have access to this cateogry.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = "B@bbb.com"
        r = self.setGetRequest('/pantry/1/')
        self.assertTrue('You do not have access to that page.' in r.data)
        
    def testCategoryIndexNoUser(self):
        '''Test the category index page with no logged in user.
        '''
        r = self.setGetRequest('/pantry/1/')
        self.assertTrue('You must log in to view that page.' in r.data)
        
    def testAddCategory1(self):
        '''Test adding a category for user A. Then test if its empyt.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'A@aaa.com'
        r = self.setPostRequest('/pantry/1/category/add/',
                                new_category_name='some grub')
        self.assertTrue('some grub' in r.data, r.data)
        expected = 'There are no items in the <b>some grub</b>' \
        ' category to display yet. Add some!'
        r = self.setGetRequest('/pantry/1/category/10/')
        self.assertTrue(expected in r.data, r.data)

    def testAddCategory2(self):
        '''Test adding a category for user C. Then test if the category is 
        empty.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'C@ccc.com'
        r = self.setPostRequest('/pantry/3/category/add/',
                                new_category_name='jalapenos')
        self.assertTrue('jalapenos' in r.data, r.data)
        expected = 'There are no items in the <b>jalapenos</b>' \
        ' category to display yet. Add some!'
        r = self.setGetRequest('/pantry/3/category/10/')
        self.assertTrue(expected in r.data, r.data)

    def testDelCategory1(self):
        '''Test deleting a category for user A.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'A@aaa.com'
        r = self.setGetRequest('/pantry/1/')
        self.assertTrue('vegetables' in r.data, 'vegetables was not' \
                        ' present before test.')
        r = self.setPostRequest('/pantry/1/category/1/delete/',
                                confirm_del=1)
        self.assertTrue('vegetables' not in r.data, r.data)
        
    def testEditCategory1(self):
        '''Test editing the veggies category, changing to 'grub' cateogry
        for user B.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'B@bbb.com'
        r = self.setPostRequest('pantry/2/category/4/edit/', 
                                updated_name='grub')
        self.assertTrue('veggies' not in r.data)
        self.assertTrue('grub' in r.data, r.data)
        
    def setSession(self, email):
        with self.app.session_transaction() as sess:
            sess['email'] = email
        
    def testDispItem1(self):
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/category/1/item/1/')
        self.assertTrue('apple' in r.data)
        self.assertTrue('shiny and red' in r.data)
        
    def testAddItem1(self):
        '''Test adding a 'grub' item to user B's pantry.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = 'B@bbb.com'
        r = self.setPostRequest('pantry/2/category/5/item/add/', 
                                new_item_name='grub',
                                quantity=1,
                                price=1,
                                description='food')
        self.assertTrue('grub' in r.data, r.data)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
