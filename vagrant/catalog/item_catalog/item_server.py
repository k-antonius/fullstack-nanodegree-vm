'''
Created on Jul 8, 2017

@author: kennethalamantia
'''
import random, string
from functools import wraps
from flask import Flask, url_for, render_template, g, request, redirect, \
abort, jsonify, session as flask_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, Category, Item

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

app.secret_key = 'development_key' # make better and move to other module
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Web client 1'


# Routes

# base
EDIT = 'edit/'
DEL = 'delete/'
ADD = 'add/'

# actual
HOME = '/'
SUCCESS = HOME + 'success/'
ERROR = HOME + 'error/'
JSON = 'json/'
LOGIN = HOME + 'login/'
LOGOUT = HOME + 'logout/'
GCONNECT = '/gconnect'

PANTRY = '/pantry/<int:pantry_id>/'
EDIT_PANTRY = PANTRY + EDIT
DEL_PANTRY = PANTRY + DEL
ADD_PANTRY = '/pantry/' + ADD
PANTRY_JSON = PANTRY + JSON

CATEGORY = PANTRY + 'category/<int:category_id>/'
EDIT_CATEGORY = CATEGORY + EDIT
DEL_CATEGORY = CATEGORY + DEL
ADD_CATEGORY = PANTRY + 'category/' + ADD

ITEM = CATEGORY + 'item/<int:item_id>/'
EDIT_ITEM = ITEM + EDIT
DEL_ITEM = ITEM + DEL
ADD_ITEM = CATEGORY + 'item/' + ADD

ALL_CATEGORIES_JSON = HOME + JSON
CATEGORY_JSON = CATEGORY + JSON
ITEM_JSON = ITEM + JSON

# templates

# general
LOGIN_TEMPLATE = "login.html"
LOGOUT_TEMPALTE = "logout.html"

# pantry
P_INDEX_TMPLT = "pantry_index.html"
P_ADD_TMPLT = "add_pantry.html"
P_DEL_TMPLT = "del_pantry.html"
P_EDIT_TMPLT = "edit_pantry.html"

# category
C_INDEX_TMPLT = "category_overview.html"
C_DISP_TMPLT = "display_category.html"
C_ADD_TMPLT = "add_category.html"
C_DEL_TMPLT = "del_category.html"
C_EDIT_TMPLT = "edit_category.html"

# item
I_ADD_TMPLT = "add_item.html"
I_DISP_TMPLT = "display_item.html"
I_DEL_TMPLT = "del_item.html"
I_EDIT_TMPLT = "edit_item.html"

# SQL Alchemy Globals
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
sessionFactory = sessionmaker(bind=engine)

# context functions

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

class DBAccessor(object):
    '''Provides access to the database as necessary.
    Serves as a mid-layer between the ORM and view functions. 
    ''' 
    
    def __init__(self):
        self.session = self._getSession()
        
    def _getSession(self):
        '''Creates a new SQL Alchemy session from the global sessionmaker
        factory object, if none exists.
        @return: SQLAlchemy Session, new or pre-existing for this app context.
        '''
        session = getattr(g, '_database', None)
        if session is None:
            session = g._database = sessionFactory()
        return session
    
    def getDBObject(self, objClass, objID):
        '''Returns an ORM object.
        @param session: SQLAlchemy session instance
        @param objClass: ORM table class
        @param objID: ORM row object
        '''
        try:
            return self.session.query(objClass).filter_by(id=objID).one()
        except:
            abort(404)
            
    def getCategoryByName(self, name):
        '''No exception is thrown if this fails.
        '''
        return self.session.query(Category).filter_by(name=name).first()
    
    def getAllCategories(self):
        '''Returns a list of all cateogies as ORM objects.
        @param session: SQL Alchemy session instance.
        '''
        try:
            return self.session.query(Category).order_by(Category.name).all()
        except:
            abort(404)
    
    
    def getAllItems(self, category_id):
        '''Returns a list of all items in a given category as a list of 
        ORM objects.
        @param session: SQL Alchemy session instance.
        @param category_id: id of the category to retrieve items from
        '''
        try:
            return self.session.query(Item).filter(Item.category_id==category_id).all()
        except:
            abort(404)
            
    def getUser(self):
        pass
    
    def adduser(self):
        pass

def loggedIn(fun):
    '''Checks if user is logged in. If not returns them to the home page
    with a flashed message.
    '''
    @wraps
    def wrapper(*args, **kwargs):
        pass

    
@app.route(HOME)
def home():
    '''Displays the home page for users that are not logged in.
    '''
    pass

@app.route(PANTRY)        
def pantryIndex():
    '''Displays all pantrys for a given user.
    '''
    pass


@app.route(ADD_PANTRY)
def addPantry():
    '''Create a new pantry
    '''
    pass


@app.route(DEL_PANTRY)
def delPantry(pantry_id):
    '''Delete a pantry
    '''
    pass


@app.route(EDIT_PANTRY)
def editPantry(pantry_id):
    '''Edit a pantry.
    '''
    pass

@app.route(HOME, methods=['GET', 'POST'])
def categoryIndex():
    '''Display the category index page.
    '''
    db = DBAccessor()
    all_categories = db.getAllCategories()
    return render_template(C_INDEX_TMPLT, categories=all_categories)

@app.route(ALL_CATEGORIES_JSON)
def getCategoriesJSON():
    '''Provides a JSON representation of the current categories in the DB.
    '''
    db = DBAccessor()
    all_categories = db.getAllCategories()
    return jsonify(all_categories=[category.serialize for category
                                   in all_categories])

@app.route(CATEGORY)
def displayCategory(category_id):
    '''Display individual category page.
    '''
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    allItems = db.getAllItems(category_id)
    return render_template(C_DISP_TMPLT, category=thisCategory, items=allItems)

@app.route(CATEGORY_JSON)
def getCategoryJSON(category_id):
    '''Return JSON for individual category.
    '''
    db = DBAccessor()
    allItems = db.getAllItems(category_id)
    return jsonify(all_items=[item.serialize for item in allItems])
    

@app.route(EDIT_CATEGORY, methods=['GET', 'POST'])
def editCategory(category_id):
    '''Edit a category entry.
    '''
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    if request.method == "POST":
        if request.form["updated_name"]:
            thisCategory.name = request.form["updated_name"]
            return redirect(url_for("categoryIndex"))
        else:
            error = "You must type a new category name."
            return render_template(C_EDIT_TMPLT,
                                   category=thisCategory,
                                   form_error=error)
    else:
        return render_template(C_EDIT_TMPLT, category=thisCategory)


@app.route(DEL_CATEGORY, methods=['GET', 'POST'])
def delCategory(category_id):
    '''Delete a category.
    '''
    # display items to be deleted.
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    allItems = db.getAllItems(category_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db.session.delete(thisCategory)
        return redirect(url_for('categoryIndex'))
    else:
        return render_template(C_DEL_TMPLT, 
                               category=thisCategory,
                               items=allItems)


@app.route(ADD_CATEGORY, methods=['GET', 'POST'])
def addCategory():
    '''Add a category.
    '''
    db = DBAccessor()
    if request.method == 'POST':
        name = request.form['new_category_name']
        if name:
            duplicate = db.getCategoryByName(name)
            if duplicate:
                return render_template(C_ADD_TMPLT, 
                                       form_error="That category already" \
                                       + " exists.")
            newCategory = Category(name=name)
            db.session.add(newCategory)
            return redirect(url_for('categoryIndex'))
        else:
            return render_template(C_ADD_TMPLT, 
                                   form_error="The name can't be blank!")
    else:
        return render_template(C_ADD_TMPLT)


@app.route(ITEM)
def displayItem(category_id, item_id):
    '''Display an item.
    '''
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    thisItem = db.getDBObject(Item, item_id)
    return render_template(I_DISP_TMPLT, category=thisCategory, item=thisItem)


@app.route(ITEM_JSON)
def getItemJSON(category_id, item_id):
    '''Return JSON for individual item.
    '''
    db = DBAccessor()
    thisItem = db.getDBObject(Item, item_id)
    return jsonify(item_info=thisItem.serialize)
    


@app.route(DEL_ITEM, methods = ['GET', 'POST'])
def delItem(category_id, item_id):
    '''Delete an item.
    '''
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    thisItem = db.getDBObject(Item, item_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db.session.delete(thisItem)
        return redirect(url_for('displayCategory', category_id=category_id))
    else:
        return render_template(I_DEL_TMPLT, category=thisCategory, item=thisItem)


@app.route(EDIT_ITEM, methods=['GET', 'POST'])
def editItem(category_id, item_id):
    '''Edit an item.
    '''
    db = DBAccessor()
    thisCategory = db.getDBObject(Category, category_id)
    thisItem = db.getDBObject(Item, item_id)
    if request.method == 'POST':
        if request.form['item_name']:
            thisItem.name = request.form['item_name']
            thisItem.quantity = request.form['quantity']
            thisItem.price = request.form['price']
            thisItem.description = request.form['description']
            return redirect(url_for('displayItem', category_id=category_id, 
                             item_id=item_id))
        else:
            return render_template(I_EDIT_TMPLT, category=thisCategory, 
                                   item=thisItem,
                                   name_error="You must provide a name.")
    else:
        return render_template(I_EDIT_TMPLT, category=thisCategory, item=thisItem)


@app.route(ADD_ITEM, methods=['GET', 'POST'])
def addItem(category_id):
    '''Add an item.
    '''
    if request.method == 'POST':
        if request.form["new_item_name"]:
            db = DBAccessor()
            newItem = Item(name=request.form["new_item_name"],
                           quantity=request.form["quantity"],
                           price=request.form["price"],
                           description=request.form["description"],
                           category_id=category_id)
            db.session.add(newItem)
            return redirect(url_for("displayCategory", category_id=category_id))
        else:
            return render_template(I_ADD_TMPLT, category=category_id,
                                   name_error="A name is required.")
    else:
        return render_template(I_ADD_TMPLT, category=category_id)


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

@app.route(LOGIN)
def login():
    state = ''.join(random.choice(string.ascii_uppercase + 
                                  string.ascii_lowercase + 
                                  string.digits)
                    for dummy_idx in xrange(32))
    flask_session['state'] = state
    return render_template(LOGIN_TEMPLATE, STATE=state)


def buildJSONResponse(msg, response_code):
    '''Helper method to build a json response.
    @param msg: object to serialize to json string
    @param response_code: http response code
    '''
    response = make_response(json.dumps(msg), response_code)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route(GCONNECT, methods=['POST'])
def gconnect():
    '''Retrieve OAuth2 state token from client request and obtain 
    authorization code from Google.
    '''
    if request.args.get('state') != flask_session['state']:
        return buildJSONResponse('Invalid state token for gConnect.', 401)
    else:
        # create credentials object
        code = request.data
        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                                 scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
            flask_session['credentials'] = credentials.to_json()
        except FlowExchangeError:
            return buildJSONResponse('Failed to create credentials object' + \
                                      ' code.', 401)
        # validate access token
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token' + \
               '=%s' % access_token)
        http_client_instance = httplib2.Http()
        result = json.loads(http_client_instance.request(url, 'GET')[1])
        if result.get('error') is not None:
            return buildJSONResponse(result.get('error'), 500)
        # Does token match this user?
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            return buildJSONResponse('Token does not match user.', 401)
        # Does token match this application?
        elif result['issued_to'] != CLIENT_ID:
            return buildJSONResponse('Token does not match application', 401)
        stored_access_token = flask_session.get('access_token')
        stored_gplus_id = flask_session.get('gplus_id')
        if (stored_access_token is not None) and (gplus_id == stored_gplus_id):
            return buildJSONResponse('Current user is already logged in: %s' \
                                     % flask_session['username'], 200)
        
        # store credentials in session
        flask_session['access_token'] = credentials.access_token
        flask_session['gplus_id'] = gplus_id
        
        # get user info from Google
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token' : credentials.access_token, 'alt' : 'json'}
        answer = requests.get(userinfo_url, params=params)
        
        data = answer.json()
        
        # set flask session keys
        flask_session['username'] = data['name']
        flask_session['picture'] = data['picture']
        flask_session['email'] = data['email']
        # check this user's authorization status 
        
        return render_template("welcome.html",
                               user=flask_session['username'],
                               picture=flask_session['picture'])
        
        
@app.route('/gdisconnect/', methods=['POST'])
def gdisconnect():
    access_token = flask_session['access_token']
    print 'In fun gdisconnect, access token is %s' % access_token
    print 'Username is'
    print flask_session['username']
    if access_token is None:
        print 'No access token.'
        return buildJSONResponse('Current user not connected.', 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
    % flask_session['access_token']
    http_client_instance = httplib2.Http()
    result = http_client_instance.request(url, 'GET')[0]
    print 'restult is: %s' % result
    if result['status'] == '200':
        del flask_session['access_token']
        del flask_session['gplus_id']
        del flask_session['username']
        del flask_session['email']
        del flask_session['picture']
        return buildJSONResponse('Successfully disconnected.', 200)
    else:
        print 'failed to revoke token'
        return buildJSONResponse('failed to revoke token', 400)
    
           

if __name__ == '__main__':
    app.debug = True
    app.run(port=5001)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    