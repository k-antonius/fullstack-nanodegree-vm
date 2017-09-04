'''
Created on Jul 8, 2017

@author: kennethalamantia
'''
import random, string
from functools import wraps
from flask import Flask, url_for, render_template, g, request, redirect, \
abort, jsonify, session as flask_session, make_response, flash

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from db_API import DBInterface
app = Flask(__name__)

app.secret_key = 'development_key' # make better and move to other module
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Web client 1'

# hooks into test code
mock_database = None

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
sessionMaker = DBInterface.makeSessionFactory()

def getDB():
    '''Creates a new SQL Alchemy session from the global sessionmaker
    factory object, if none exists.
    @return: SQLAlchemy Session, new or pre-existing for this app context.
    '''
    db = getattr(g, '_database', None)
    if db is None:
        if app.testing:
            assert mock_database is not None, "mock db not initialized"
            g._database = DBInterface(mock_database, testing=True)
        else:
            session = sessionMaker()
            g._database = DBInterface(session=session)
    return g._database
    

@app.teardown_appcontext
def teardown_session(exception):
    '''Closes the SQLAlchemy session.
    @param exception: any exception raised during the this context
    '''
    if not app.testing:
        db_interface = getattr(g, '_database', None)
        if db_interface:
            if exception:
                db_interface.db.session.rollback()
            else:
                try:
                    db_interface.db.session.commit()
                finally:
                    db_interface.db.session.close()
#     g._database = None


def isLoggedIn(fun):
    '''Checks to see if a user is logged in.
    '''
    @wraps(fun)
    def wrapper(*args, **kwargs):
        user_email = flask_session.get('email')
        if user_email is not None:
            db = getDB()
            user = db.getUserByEmail(user_email)
            if user is not None:
                kwargs['user'] = user
                return fun(*args, **kwargs)
            else:
                return abort(404)
        else:
            flash('You must log in to view that page.')
            return redirect(url_for('login'))
    return wrapper


def isAuthorized(fun):
    '''Checks whether a user is logged in and authorized to view a page.
    '''
    @wraps(fun)
    def wrapper(*args, **kwargs):
        user_email = flask_session.get('email')
        if user_email is not None:
            db = getDB()
            user = db.getUserByEmail(user_email)
            if user is not None:
                pantry_id = kwargs.get('pantry_id')
                assert pantry_id, "This function requires a pantry id."
                pantry = db.getDBObjectById('Pantry', pantry_id)
                if pantry in db.getAuthorizedPantries(user):
                    kwargs['user'] = user
                    return fun(*args, **kwargs)
                else:
                    flash('You do not have access to that page.')
                    return redirect(url_for('pantryIndex'))
            else:
                return abort(404)
        else:
            flash('You must log in to view that page.')
            return redirect(url_for('login'))
    return wrapper

    
@app.route(HOME)
def home():
    '''Displays the home page for users that are not logged in.
    '''
    pass

@app.route('/pantry/')
@isLoggedIn
def pantryIndex(user, **kwargs):
    '''Displays all pantrys for a given user.
    '''
    db = getDB()
    all_pantries = db.getAuthorizedPantries(user)
    return render_template(P_INDEX_TMPLT,
                           pantries=all_pantries)

@app.route(ADD_PANTRY, methods=['GET', 'POST'])
@isLoggedIn
def addPantry(user, **kwargs):
    '''Create a new pantry.
    '''
    db = getDB()
    if request.method == 'POST':
        name = request.form['new_pantry_name']
        if name:
            duplicate = db.getDBObjectByName('Pantry', name, user.id)
            if duplicate:
                return render_template(P_ADD_TMPLT,
                                       form_error='You already have a pantry' \
                                       ' with that name.' \
                                       ' Please choose another.')
            db.addObject('Pantry', name, user.id)
            return redirect(url_for('pantryIndex'))
        else:
            return render_template(P_ADD_TMPLT,
                                   form_error="The name can't be blank.")
    else: 
        return render_template(P_ADD_TMPLT)


@app.route(DEL_PANTRY, methods=['GET', 'POST'])
@isAuthorized
def delPantry(user, pantry_id, **kwargs):
    '''Delete a pantry
    '''
    db = getDB()
    thisPantry = db.getDBObjectById('Pantry', user.id)
    allCategories = db.getAllObjects('Category', pantry_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db.delObject(thisPantry)
        return redirect(url_for('pantryIndex'))
    else:
        return render_template(P_DEL_TMPLT,
                               pantry = thisPantry,
                               categories = allCategories)
      

@app.route(EDIT_PANTRY, methods=['GET', 'POST'])
@isLoggedIn
def editPantry(user, pantry_id, **kwargs):
    '''Edit a pantry.
    '''
    db = getDB()
    thisPantry = db.getDBObjectById('Pantry', pantry_id)
    if request.method == 'POST':
        editedName = request.form.get('updated_name')
        if editedName:
            thisPantry.name = editedName
            return redirect(url_for('pantryIndex'))
        else:
            error = 'The pantry name cannot be blank.'
            return render_template(P_EDIT_TMPLT, pantry=thisPantry,
                                   form_error=error)
    else:
        return render_template(P_EDIT_TMPLT, pantry=thisPantry)
             

@app.route(PANTRY_JSON)
@isLoggedIn
def getPantriesJSON(user, **kwargs):
    '''Display JSON for this user's pantries. Does not display shared pantries.
    '''
    db = getDB()
    allPantries = db.getAllObjects("Pantry", user.id)
    return jsonify(allPantries=[pantry.serialize for pantry in allPantries])


@app.route(PANTRY, methods=['GET', 'POST'])
@isAuthorized
def categoryIndex(pantry_id, **kwargs):
    '''Display the category index page.
    '''
    db = getDB()
    all_categories = db.getAllObjects('Category', pantry_id)
    return render_template(C_INDEX_TMPLT, 
                           categories=all_categories,
                           pantry_id=pantry_id)
    
@app.route(ALL_CATEGORIES_JSON)
@isAuthorized
def getCategoriesJSON(pantry_id, **kwargs):
    '''Provides a JSON representation of the current categories in the pantry.
    '''
    db = getDB()
    all_categories = db.getAllObjects('Category', pantry_id)
    return jsonify(all_categories=[category.serialize for category
                                   in all_categories])
@app.route(CATEGORY)
@isAuthorized
def displayCategory(pantry_id, category_id, **kwargs):
    '''Display individual category page.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    allItems = db.getAllObjects('Item', category_id)
    return render_template(C_DISP_TMPLT, category=thisCategory, items=allItems,
                           pantry_id=pantry_id)
@app.route(CATEGORY_JSON)
@isAuthorized
def getCategoryJSON(pantry_id, category_id, **kwargs):
    '''Return JSON for individual category.
    '''
    db = getDB()
    allItems = db.getAllObjects('Item', category_id)
    return jsonify(all_items=[item.serialize for item in allItems])
    
@app.route(EDIT_CATEGORY, methods=['GET', 'POST'])
@isAuthorized
def editCategory(pantry_id, category_id, **kwargs):
    '''Edit a category entry.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    if request.method == "POST":
        if request.form["updated_name"]:
            thisCategory.name = request.form["updated_name"]
            return redirect(url_for("categoryIndex", pantry_id=pantry_id))
        else:
            error = "You must type a new category name."
            return render_template(C_EDIT_TMPLT,
                                   category=thisCategory,
                                   form_error=error)
    else:
        return render_template(C_EDIT_TMPLT, category=thisCategory)

@app.route(DEL_CATEGORY, methods=['GET', 'POST'])
@isAuthorized
def delCategory(pantry_id, category_id, **kwargs):
    '''Delete a category.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    allItems = db.getAllObjects('Item', category_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db.delObject(thisCategory)
        return redirect(url_for('categoryIndex', pantry_id=pantry_id))
    else:
        return render_template(C_DEL_TMPLT, 
                               category=thisCategory,
                               items=allItems,
                               pantry_id=pantry_id)

@app.route('/pantry/<int:pantry_id>/category/add/', methods=['GET', 'POST'])
@isAuthorized
def addCategory(pantry_id, **kwargs):
    '''Add a category.
    '''
    db = getDB()
    if request.method == 'POST':
        name = request.form['new_category_name']
        if name:
            duplicate = db.getDBObjectByName('Category', name, pantry_id)
            if duplicate:
                return render_template(C_ADD_TMPLT, 
                                       form_error="That category already" \
                                       + " exists.")
            db.addObject('Category', name, pantry_id)
            return redirect(url_for('categoryIndex', pantry_id=pantry_id))
        else:
            return render_template(C_ADD_TMPLT, 
                                   form_error="The name can't be blank!")
    else:
        return render_template(C_ADD_TMPLT)

@app.route(ITEM)
@isAuthorized
def displayItem(pantry_id, category_id, item_id, **kwargs):
    '''Display an item.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    thisItem = db.getDBObjectById('Item', item_id)
    return render_template(I_DISP_TMPLT,
                           pantry_id=pantry_id,
                           category=thisCategory, item=thisItem)

@app.route(ITEM_JSON)
@isAuthorized
def getItemJSON(pantry_id, category_id, item_id, **kwargs):
    '''Return JSON for individual item.
    '''
    db = getDB()
    thisItem = db.getDBObjectById('Item', item_id)
    return jsonify(item_info=thisItem.serialize)
    

@app.route(DEL_ITEM, methods = ['GET', 'POST'])
@isAuthorized
def delItem(pantry_id, category_id, item_id, **kwargs):
    '''Delete an item.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    thisItem = db.getDBObjectById('Item', item_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db.delObject(thisItem)
        return redirect(url_for('displayCategory',
                                pantry_id=pantry_id, category_id=category_id))
    else:
        return render_template(I_DEL_TMPLT, pantry_id=pantry_id,
                               category=thisCategory, item=thisItem)

@app.route(EDIT_ITEM, methods=['GET', 'POST'])
@isAuthorized
def editItem(pantry_id, category_id, item_id, **kwargs):
    '''Edit an item.
    '''
    db = getDB()
    thisCategory = db.getDBObjectById('Category', category_id)
    thisItem = db.getDBObjectById('Item', item_id)
    if request.method == 'POST':
        if request.form['item_name']:
            thisItem.name = request.form['item_name']
            thisItem.quantity = request.form['quantity']
            thisItem.price = request.form['price']
            thisItem.description = request.form['description']
            return redirect(url_for('displayItem', pantry_id=pantry_id, 
                                    category_id=category_id, item_id=item_id))
        else:
            return render_template(I_EDIT_TMPLT,
                                   pantry_id=pantry_id,
                                   category=thisCategory, 
                                   item=thisItem,
                                   name_error="You must provide a name.")
    else:
        return render_template(I_EDIT_TMPLT,
                               pantry_id=pantry_id,
                               category=thisCategory, 
                               item=thisItem)

@app.route(ADD_ITEM, methods=['GET', 'POST'])
@isAuthorized
def addItem(pantry_id, category_id, **kwargs):
    '''Add an item.
    '''
    if request.method == 'POST':
        if request.form["new_item_name"]:
            db = getDB()
            db.addObject('Item',
                         request.form["new_item_name"],
                         request.form["quantity"],
                         request.form["price"],
                         request.form["description"],
                         category_id)
            return redirect(url_for("displayCategory",
                                    pantry_id=pantry_id,
                                    category_id=category_id))
        else:
            return render_template(I_ADD_TMPLT, category=category_id,
                                   name_error="A name is required.")
    else:
        return render_template(I_ADD_TMPLT, category=category_id)


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

def checkUser():
    '''Checks to see whether this user has used the app before. If not, 
    is adds the user to the database. If the user has, this updates their
    username if necessary.  The user's info comes directly from
    the flask session, so it is an error to call this method when the
    session is empty.
    '''
    db = getDB()
    user = db.getUserByEmail(flask_session['email'])
    if user is not None:
        if user.name != flask_session['username']:
            user.name = flask_session['username']
    else:
        user = db.addObject('User', flask_session['username'],
                            flask_session['email'])
    

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
        checkUser() 
         
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    