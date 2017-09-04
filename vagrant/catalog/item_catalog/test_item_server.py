'''
Created on Aug 5, 2017

@author: kennethalamantia
'''
import os
import item_server
import unittest
from test_db_populator import User, Category, Pantry, Item, MockDB
from db_API import DBInterface
from actual_db_populator import MockDB as Mock


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
    
    def setSession(self, email):
        '''Helper method to set user email cookie for session so that user is
        logged in.
        '''
        with self.app.session_transaction() as sess:
            sess['email'] = email
        
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
        
    def testAddPantry(self):
        '''Test adding a pantry to user A's pantry access list.
        '''
        self.setSession('A@aaa.com')
        r = self.setPostRequest('/pantry/add/',
                                new_pantry_name='grub')
        self.assertTrue('grub' in r.data, r.data)
        
    def testAddPantryDuplicate(self):
        '''Test adding pantry with duplicate name.
        '''
        self.setSession("A@aaa.com")
        r = self.setPostRequest("/pantry/add/",
                                new_pantry_name="Pantry_A")
        expected = "You already have a pantry with that name. Please choose" \
        " another."
        self.assertTrue(expected in r.data, r.data)
        
    def testAddPantryNoName(self):
        '''Test added a pantry with the name field blank.
        '''
        self.setSession('C@ccc.com')
        r = self.setPostRequest('/pantry/add/', new_pantry_name='')
        expected = "The name can't be blank."
        self.assertTrue(expected in r.data, r.data)
        
    def testDelPantry(self):
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/')
        self.assertTrue('Pantry_A' in r.data, r.data)
        r = self.setPostRequest('/pantry/1/delete/', confirm_del=1)
        self.assertFalse('Pantry_A' in r.data, r.data)
        
    def testDelPantryForm(self):
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/delete/')
        self.assertTrue('Pantry_A' in r.data, r.data)
        self.assertTrue('vegetables' in r.data, r.data)
        self.assertTrue('starches' in r.data, r.data)
        self.assertTrue('desserts' in r.data, r.data)
        
    def testEditPantry(self):
        self.setSession('B@bbb.com')
        gr = self.setGetRequest('/pantry/2/edit/')
        self.assertTrue('Pantry_B' in gr.data, gr.data)
        pr = self.setPostRequest('/pantry/2/edit/', updated_name='B_Pantry')
        self.assertTrue('B_Pantry' in pr.data, pr.data)
        self.assertTrue('Pantry_B' not in pr.data, pr.data)
        
    def testEditPantryNoName(self):
        self.setSession('B@bbb.com')
        r = self.setPostRequest('/pantry/2/edit/', updated_name = '')
        self.assertTrue('Pantry_B' in r.data, r.data)
        self.assertTrue('The pantry name cannot be blank.' in r.data, r.data)
        
    def testPantryJSON(self):
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/json/')
        self.assertTrue('Pantry_A' in r.data, r.data)
        self.assertTrue('1' in r.data, r.data)
        self.assertTrue('Pantry_D' in r.data, r.data)
        self.assertTrue('4' in r.data, r.data)
    
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
        self.setSession('B@bbb.com')
        r = self.setGetRequest('/pantry/2/category/4/edit')
        self.assertTrue('veggies' in r.data, r.data)
        r = self.setPostRequest('pantry/2/category/4/edit/', 
                                updated_name='grub')
        self.assertTrue('veggies' not in r.data)
        self.assertTrue('grub' in r.data, r.data)

    def testEditCategoryError(self):
        '''Test editing a category to have no name
        '''
        self.setSession('C@ccc.com')
        r = self.setPostRequest('/pantry/3/category/7/edit/',
                                updated_name = '')
        self.assertTrue('You must type a new category name.' in r.data, r.data)
    
    def testCategoryJSON(self):
        '''Test displaying JSON for category.
        '''
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/category/1/json')
        self.assertTrue('apple' and 'broccoli' in r.data, r.data)
        
    def testDispItem1(self):
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/category/1/item/1/')
        self.assertTrue('apple' in r.data)
        self.assertTrue('shiny and red' in r.data)
        
    def testAddItem1(self):
        '''Test adding a 'grub' item to user B's pantry.
        '''
        self.setSession('B@bbb.com')
        r = self.setPostRequest('pantry/2/category/5/item/add/', 
                                new_item_name='grub',
                                quantity=1,
                                price=1,
                                description='food')
        self.assertTrue('grub' in r.data, r.data)
        
    def testAddItemNoName(self):
        '''Test for adding an item without a name. Tests for error message.
        '''
        self.setSession('A@aaa.com')
        r = self.setPostRequest('/pantry/1/category/1/item/add/',
                                new_item_name='',
                                quantity=1,
                                price=1,
                                description='food')
        self.assertTrue('A name is required.' in r.data, r.data)
        
    def testAddItemForm(self):
        '''Test that get request displays add item form.
        '''
        self.setSession('C@ccc.com')
        r = self.setGetRequest('/pantry/3/category/7/item/add/')
        self.assertTrue('Type information about your new item:' in r.data,
                        r.data)
        
    def testDelItem1(self):
        '''Test deleting broccoli from user A's pantry.
        '''
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/category/1/')
        self.assertTrue('apple' in r.data)
        r = self.setPostRequest('/pantry/1/category/1/item/1/delete/',
                                confirm_del=1)
        self.assertTrue('apple' not in r.data)
    
    def testDelItemForm(self):
        '''Test get request to this view function displays the delete form.
        Ensure the proper items are displayed.
        '''
        self.setSession('B@bbb.com')
        r = self.setGetRequest('/pantry/3/category/8/item/4/delete/')
        self.assertTrue('steak' in r.data, r.data)
        expected = 'Are you sure you want to delete the <b>steak</b> item from'\
        ' the <b>meat</b> category?'
        self.assertTrue(expected in r.data, r.data)
        
    def testEditItem1(self):
        '''Test successfully editing an item. Display the form first.
        '''
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/2/category/5/item/3/edit/')
        self.assertTrue('chips' in r.data, r.data)
        r = self.setPostRequest('/pantry/2/category/5/item/3/edit/',
                                item_name='chipz',
                                quantity=1,
                                price=1,
                                description='chips but cooler')
        self.assertTrue('chipz' in r.data, r.data)
        self.assertFalse('chips' not in r.data)

    def testEditItemError(self):
        '''Test editing an item and not adding the name back. Renders
        an error msg.
        '''
        self.setSession('A@aaa.com')
        r = self.setPostRequest('/pantry/2/category/5/item/3/edit/',
                                item_name='',
                                quantity=1,
                                price=1,
                                description='chips but cooler')
        self.assertTrue('You must provide a name' in r.data, r.data)
        self.assertTrue('chips' in r.data, r.data)
        
    def testItemJSON(self):
        '''Test displaying JSON for an item.
        '''
        self.setSession('A@aaa.com')
        r = self.setGetRequest('/pantry/1/category/1/item/1/json/')
        self.assertTrue('apple' and 'shiny and red' in r.data, r.data)

class TestDatabase(unittest.TestCase):
    def setUp(self):
        mock = Mock()
        mock.populate()
        session_maker = DBInterface.makeSessionFactory(testing=True)
        session = session_maker()
        self.db = DBInterface(session)
    
    # Test get by id ------
        
    def testGetUserById(self):
        '''Test getting a user by id.
        '''
        expected_0 = 'A'
        expected_1 = 'A@aaa.com'
        user = self.db.getDBObjectById('User', 1)
        self.assertEqual(user.name, expected_0)
        self.assertEqual(user.email, expected_1)
    
    def testGetPantryById(self):
        '''Test getting a specific pantry by id.
        '''
        expected_0 = 'Pantry_B'
        pantry = self.db.getDBObjectById('Pantry', 2)
        self.assertEqual(pantry.name, expected_0)
    
    def testGetCategoryById(self):
        '''Test getting a category by id.
        '''
        expected_0 = 'desserts'
        category = self.db.getDBObjectById('Category', 3)
        self.assertEqual(category.name, expected_0)
    
    def testGetItemById(self):
        '''Test getting an item by id.
        '''
        expected_0 = 'steak'
        expected_1 = 'high in protein'
        expected_2 = 8
        item = self.db.getDBObjectById('Item', 4)
        self.assertEqual(item.name, expected_0)
        self.assertEqual(item.description, expected_1)
        self.assertEqual(item.parent_id, expected_2)
        
    # Test get all associated with a specific parent
    
    def testGetAllPantries(self):
        '''Test getting all the pantries user A owns.
        '''
        expected = ['Pantry_A', 'Pantry_D']
        pantryObjList = self.db.getAllObjects('Pantry', 1)
        self.assertEqual(expected, [pantry.name for pantry in pantryObjList])

    def testGetAllCategories(self):
        '''Test getting all the categories associated with Pantry C
        '''
        expected = ['fruit', 'meat', 'drinks']
        categoryObjList = self.db.getAllObjects('Category', 3)
        self.assertEqual(expected, [category.name for category in \
                                    categoryObjList])      
    
    def testGetAllItems(self):
        '''Test getting all items associated with category with id 1.
        '''
        expected = ['apple', 'broccoli']
        itemObjList = self.db.getAllObjects('Item', 1)
        self.assertEqual(expected, [item.name for item in itemObjList])
        
    # Test get object by name, associated with a specific parent.
    
    def testGetPantryByName(self):
        '''Test getting Pantry_A by name.
        '''
        pantryObj = self.db.getDBObjectByName('Pantry', 'Pantry_A', 1)
        self.assertEqual('Pantry_A', pantryObj.name)
        
    def testGetCategoryByName(self):
        '''Test getting the snacks category by name from Pantry B
        '''
        categoryObj = self.db.getDBObjectByName('Category', 'snacks', 2)
        self.assertEqual('snacks', categoryObj.name)
    
    def testgetItemByName(self):
        '''Test getting the seltzer item by name
        '''
        itemObj = self.db.getDBObjectByName('Item', 'seltzer', 3)
        self.assertEqual('seltzer', itemObj.name)
    
    # Test get User by email (equivalent of name)
    
    def testGetUserByEmail1(self):
        '''Test getting user A by email
        '''
        user = self.db.getUserByEmail('A@aaa.com')
        self.assertEqual('A@aaa.com', user.email)
    
    def testGetUserByEmail2(self):
        '''Test getting user C by email.
        '''
        user = self.db.getUserByEmail('C@ccc.com')
        self.assertEqual('C@ccc.com', user.email)
    
    # Test getting all the pantries a user has access to, owned and shared

    def testAuthPantries1(self):
        '''Test getting the pantries user A can access.
        '''
        user = self.db.getUserByEmail('A@aaa.com')
        pantries = self.db.getAuthorizedPantries(user)
        self.assertEqual(['Pantry_A', 'Pantry_B', 'Pantry_D'],
                         [pantry.name for pantry in pantries])
    
    def testAuthPantries2(self):
        '''Test getting the pantries that user B can access.
        '''
        user = self.db.getUserByEmail('B@bbb.com')
        pantries = self.db.getAuthorizedPantries(user)
        self.assertEqual(['Pantry_B'], [pantry.name for pantry in pantries])
    
    # Test adding objects
    
    def testAddUser(self):
        '''Test adding User D to the database.
        '''
        self.assertTrue(self.db.getUserByEmail('D@ddd.com') is None)
        self.db.addObject('User', 'D', 'D@ddd.com')
        self.db._commit()
        user_D = self.db.getUserByEmail('D@ddd.com')
        self.assertEqual(user_D.name, 'D')
        self.assertEqual(user_D.children, [])
        
    def testAddPantry(self):
        '''Test adding a pantry owned by User C.
        '''
        self.assertEqual(self.db.getDBObjectByName('Pantry', 'Pantry_E', 3),
                         None)
        self.db.addObject('Pantry', 'Pantry_E', 3)
        self.db._commit()
        actual = self.db.getDBObjectByName('Pantry', 'Pantry_E', 3)
        expected = 'Pantry_E'
        self.assertEqual(expected, actual.name)
        user_c = self.db.getUserByEmail('C@ccc.com')
        pantries = self.db.getAuthorizedPantries(user_c)
        self.assertTrue(actual in pantries, "Pantry was not added to "\
                        "user pantries list.")
        
    def testAddCategory(self):
        '''Test add category to Pantry B
        '''
        self.assertEqual(self.db.getDBObjectByName('Category', 'fruit', 2),
                         None)
        self.db.addObject('Category', 'fruit', 2)
        self.db._commit()
        actual = self.db.getDBObjectByName('Category', 'fruit', 2)
        expected = 'fruit'
        self.assertEqual(actual.name, expected, 'fruit not in pantry' \
                         ' PantryB')
        pantry_B = self.db.getDBObjectById('Pantry', 2)
        self.assertTrue(actual in pantry_B.children)
        
    def testAddItem(self):
        '''Test adding an item to the vegetables category in pantry A.
        '''
        self.assertEqual(self.db.getDBObjectByName('Item', 'grub', 1), None)
        self.db.addObject('Item', 'grub', 'a great food', 3, 4, 1)
        self.db._commit()
        actual = self.db.getDBObjectByName('Item', 'grub', 1)
        expected = 'grub'
        self.assertEqual(actual.name, expected, 'grub item not in Pantry A.')
        self.assertEqual(actual.description, 'a great food')
        self.assertEqual(actual.quantity, 3)
        self.assertEqual(actual.price, 4)
        vegetable_category = self.db.getDBObjectById('Category', 1)
        self.assertTrue(actual in vegetable_category.children)
    
    # Test deleting objects
    def testDelUserA(self):
        '''Test deleting user A. Make sure the delete cascades.
        '''
        user_A = self.db.getUserByEmail('A@aaa.com')
        user_B = self.db.getUserByEmail('B@bbb.com')
        self.assertTrue(user_A is not None, 'failed sanity check')
        pantry_A = self.db.getDBObjectByName('Pantry', 'Pantry_A', 1)
        pantry_B = self.db.getDBObjectByName('Pantry', 'Pantry_B', 2)
        self.assertTrue(pantry_B is \
                        not None, 'failed sanity check')
        self.assertTrue(user_B in pantry_B.users, 'failed sanity check')
        self.assertTrue((pantry_A in user_A.children, 'Pantry A not in '\
                         'children list for User A.'))
        self.db.delObject(user_A)
        self.db._commit()
        no_user = self.db.getUserByEmail('A@aaa.com')
        self.assertTrue(no_user is None, 'failed to delete user')
        # test cascading
        self.assertTrue(self.db.getDBObjectByName('Pantry', 'Pantry_A', 1) is \
                        None)
        self.assertTrue(self.db.getDBObjectByName('Pantry', 'Pantry_B', 2) is \
                        not None, 'Pantry B, which was only shared with user' \
                        ' A should not have been deleted.')
        pantry_D = self.db.getDBObjectByName('Pantry', 'Pantry_D', 1)
        self.assertTrue(pantry_D is None)
        
    def testDelPantry(self):
        '''Test deleting Pantry B. Make sure the deletion cascades.
        '''
        # sanity checks
        pantry_B = self.db.getDBObjectById('Pantry', 2)
        self.assertTrue(len(pantry_B.children) == 3, 'failed sanity check')
        self.db.delObject(pantry_B)
        self.db._commit()
        pantry_B = self.db.getDBObjectByName('Pantry', 'Pantry_B', 2)
        self.assertEquals(pantry_B, None)
        self.assertEquals(self.db.getDBObjectByName('Item', 'chips', 5), None)
        self.assertEquals(self.db.getDBObjectByName('Category', 'veggies', 2),
                          None)
        
    def testDelCategory(self):
        '''Test deleting fuit category from Pantry C
        '''
        fruit = self.db.getDBObjectByName('Category', 'fruit', 3)
        self.assertTrue(fruit is not None, 'failed sanity check')
        self.assertTrue(fruit.children[0].name == 'apple', 
                        'failed sanity check')
        pantry_c = self.db.getDBObjectById('Pantry', 3)
        len_before = len(pantry_c.children)
        self.db.delObject(fruit)
        self.db._commit()
        noFruit = self.db.getDBObjectByName('Category', 'fruit', 3)
        self.assertTrue(noFruit is None, 'fruit not deleted')
        self.assertEquals(None,
                          self.db.getDBObjectByName('Item', "apple", 7))
        len_after = len(self.db.getDBObjectById('Pantry', 3).children)
        self.assertNotEqual(len_before, len_after,
                            'len before was {0} and len after was {1}'\
                            .format(len_before, len_after))
        
    def testDelItem(self):
        '''Test deleting apple item from pantry A
        '''
        apple = self.db.getDBObjectByName('Item', 'apple', 1)
        self.assertIsNotNone(apple, 'failed sanity check')
        len_before = len(self.db.getDBObjectById('Category', 1).children)
        self.db.delObject(apple)
        self.db._commit()
        noApple = self.db.getDBObjectByName('Item', 'apple', 1)
        self.assertIsNone(noApple, 'apple failed to delete')
        len_after = len(self.db.getDBObjectById('Category', 1).children)
        self.assertNotEqual(len_before, len_after,
                            'len before was {0} and len after was {1}'\
                            .format(len_before, len_after))

    # Test updating objects
    def testUpdateUser(self):
        '''Test updating user A attributes.
        '''
        pass
        
    def testUpdatePantry(self):
        '''Test updating pantry B attributes.
        '''
        pass
        
    def testUpdateCategory(self):
        '''
        '''
        pass
    
    def testUpdateItem(self):
        '''
        '''
        pass
    
    def teardown(self):
        self.db._close()
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    






















