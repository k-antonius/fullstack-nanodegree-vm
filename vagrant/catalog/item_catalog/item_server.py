'''
Created on Jul 8, 2017

@author: kennethalamantia
'''
from flask import Flask, url_for, render_template
app = Flask(__name__)

# Routes

# base
EDIT = 'edit/'
DEL = 'delete/'
ADD = 'add/'

# actual
HOME = '/'
SUCCESS = HOME + 'success/'
ERROR = HOME + 'error/'

CATEGORY = '/category/<int:category_id>/'
EDIT_CATEGORY = CATEGORY + EDIT
DEL_CATEGORY = CATEGORY + DEL
ADD_CATEGORY = CATEGORY + ADD

ITEM = CATEGORY + 'item/<int:item_id>/'
EDIT_ITEM = ITEM + EDIT
DEL_ITEM = ITEM + DEL
ADD_ITEM = ITEM + ADD


@app.route(HOME)
def home():
    '''Display the home page.
    '''
    return 'This is the home page.'


@app.route(CATEGORY)
def dispCategory(category_id):
    '''Display individual category page.
    '''
    return 'This is an individual category page.'


@app.route(EDIT_CATEGORY)
def editCategory(category_id):
    '''Edit a category entry.
    '''
    return 'edit a category.'

@app.route(DEL_CATEGORY)
def delCategory(cateogry_id):
    '''Delete a category.
    '''
    return 'delete a category.'


@app.route(ADD_CATEGORY)
def addCategory(category_id):
    '''Add a category.
    '''
    return 'add a category'


@app.route(ITEM)
def displayItem(category_id, item_id):
    '''Display an item.
    '''
    return 'individual item page.'


@app.route(DEL_ITEM)
def delItem(category_id, item_id):
    '''Delete an item.
    '''
    return 'delete an item'


@app.route(EDIT_ITEM)
def ediItem(level_1_id, level_2_id):
    '''Edit an item.
    '''
    return 'edit an item'


@app.route(ADD_ITEM)
def addItem(level_1_id, level_2_id):
    '''Add an item.
    '''
    return 'add an item'


@app.route(SUCCESS)
def successUpdate():
    '''Page displayed when CRUD operation successful.
    '''
    return 'Operation successful.'


@app.route(ERROR)
def errorUpdate():
    '''Page displayed when CRUD operation fails.
    '''
    return 'Error. Operation unsuccessful.'


if __name__ == '__main__':
    app.debug = True
    app.run()