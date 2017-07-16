'''
Created on Jul 8, 2017

@author: kennethalamantia
'''
from flask import Flask, url_for, render_template, g, request, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, Category, Item
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
ADD_CATEGORY = '/category/' + ADD

ITEM = CATEGORY + 'item/<int:item_id>/'
EDIT_ITEM = ITEM + EDIT
DEL_ITEM = ITEM + DEL
ADD_ITEM = CATEGORY + 'item/' + ADD

# SQL Alchemy Globals
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
sessionFactory = sessionmaker(bind=engine)

# context functions
def getSession():
    '''Creates a new SQL Alchemy session from the global sessionmaker
    factory object, if none exists.
    @return: SQLAlchemy Session, new or pre-existing for this app context.
    '''
    session = getattr(g, '_database', None)
    if session is None:
        session = sessionFactory()
    return session


@app.teardown_appcontext
def teardown_session(exception=None):
    '''Closes the SQLAlchemy session.
    @param exception: any exception raised during the this context
    '''
    session = getattr(g, '_database', None)
    if session:
        if exception:
            session.rollback()
        else:
            try:
                session.commit()
            finally:
                session.close()


@app.route(HOME)
def home():
    '''Display the home page.
    '''
    session = getSession()
    all_categories = session.query(Category).order_by(Category.name).all()
    return render_template("category_overview.html", categories=all_categories)


@app.route(CATEGORY)
def displayCategory(category_id):
    '''Display individual category page.
    '''
    return 'This is an individual category page.'


@app.route(EDIT_CATEGORY)
def editCategory(category_id):
    '''Edit a category entry.
    '''
    return 'edit a category.'


@app.route(DEL_CATEGORY, methods=['GET', 'POST'])
def delCategory(category_id):
    '''Delete a category.
    '''
    session = getSession()
    thisCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST' and request.form['confirm_del']:
        session.delete(thisCategory)
        session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("del_category.html", items=[], category=thisCategory)


@app.route(ADD_CATEGORY, methods=['GET', 'POST'])
def addCategory():
    '''Add a category.
    '''
    if request.method == 'POST':
        name = request.form['new_category_name']
        if name:
            session = getSession()
            duplicate = session.query(Category).filter_by(name=name).one()
            if duplicate:
                return render_template("add_category.html", 
                                       form_error="That category already" \
                                       + " exists.")
            newCategory = Category(name=name)
            session.add(newCategory)
            session.commit()
            return redirect(url_for('home'))
        else:
            return render_template("add_category.html", 
                                   form_error="The name can't be blank!")
    else:
        return render_template("add_category.html")


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
    app.run(port=5001)