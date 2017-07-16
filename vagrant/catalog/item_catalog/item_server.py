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

# templates

# category
CAT_OVERVIEW = "category_overview.html"
CAT_DISP = "display_category.html"
CAT_ADD = "add_category.html"
CAT_DEL = "del_category.html"
CAT_EDIT = "edit_category.html"

# item
ITEM_ADD = "add_item.html"

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
        session = g._database = sessionFactory()
    return session


@app.teardown_appcontext
def teardown_session(exception):
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
    return render_template(CAT_OVERVIEW, categories=all_categories)


@app.route(CATEGORY)
def displayCategory(category_id):
    '''Display individual category page.
    '''
    return 'This is an individual category page.'


@app.route(EDIT_CATEGORY, methods=['GET', 'POST'])
def editCategory(category_id):
    '''Edit a category entry.
    '''
    session = getSession()
    thisCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == "POST":
        if request.form["updated_name"]:
            thisCategory.name = request.form["updated_name"]
            return redirect(url_for("home"))
        else:
            error = "You must type a new category name."
            return render_template(CAT_EDIT,
                                   category=thisCategory,
                                   form_error=error)
    else:
        return render_template(CAT_EDIT, category=thisCategory)


@app.route(DEL_CATEGORY, methods=['GET', 'POST'])
def delCategory(category_id):
    '''Delete a category.
    '''
    session = getSession()
    thisCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST' and request.form['confirm_del']:
        session.delete(thisCategory)
        return redirect(url_for('home'))
    else:
        return render_template(CAT_DEL, items=[], 
                               category=thisCategory)


@app.route(ADD_CATEGORY, methods=['GET', 'POST'])
def addCategory():
    '''Add a category.
    '''
    if request.method == 'POST':
        name = request.form['new_category_name']
        if name:
            session = getSession()
            duplicate = session.query(Category).filter_by(name=name).first()
            if duplicate:
                return render_template(CAT_ADD, 
                                       form_error="That category already" \
                                       + " exists.")
            newCategory = Category(name=name)
            session.add(newCategory)
            session.commit()
            return redirect(url_for('home'))
        else:
            return render_template(CAT_ADD, 
                                   form_error="The name can't be blank!")
    else:
        return render_template(CAT_ADD)


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
def editItem(level_1_id, level_2_id):
    '''Edit an item.
    '''
    return 'edit an item'


@app.route(ADD_ITEM, methods=['GET', 'POST'])
def addItem(category_id):
    '''Add an item.
    '''
    if request.method == 'POST':
        if request.form["new_item_name"]:
            session = getSession()
            newItem = Item(name=request.form["new_item_name"],
                           quantity=request.form["quantity"],
                           price=request.form["price"],
                           description=request.form["description"],
                           category_id=category_id)
            session.add(newItem)
            return redirect(url_for("displayCategory", category_id=category_id))
        else:
            return render_template(ITEM_ADD, category=category_id,
                                   name_error="A name is required.")
    else:
        return render_template(ITEM_ADD, category=category_id)


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