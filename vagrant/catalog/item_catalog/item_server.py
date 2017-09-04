'''
Created on Jul 8, 2017

@author: kennethalamantia
'''
import random, string
from functools import wraps
import json
from flask import Flask, url_for, render_template, g, request, redirect, \
abort, jsonify, session as flask_session, make_response, flash

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests
from item_catalog.db_API import DBInterface
app = Flask(__name__)

app.secret_key = 'development_key'  # make better and move to other module
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
session_maker = DBInterface.make_session_factory()

def get_db_api():
    '''Creates a new SQL Alchemy session from the global sessionmaker
    factory object, if none exists.
    @return: SQLAlchemy Session, new or pre-existing for this app context.
    '''
    db_api = getattr(g, '_database', None)
    if db_api is None:
        if app.testing:
            assert mock_database is not None, "mock database not initialized"
            g._database = DBInterface(mock_database, testing=True)
        else:
            session = session_maker()
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


def is_logged_in(fun):
    '''Checks to see if a user is logged in.
    '''
    @wraps(fun)
    def wrapper(*args, **kwargs):
        user_email = flask_session.get('email')
        if user_email is not None:
            db_api = get_db_api()
            user = db_api.get_user_by_email(user_email)
            if user is not None:
                kwargs['user'] = user
                return fun(*args, **kwargs)
            else:
                return abort(404)
        else:
            flash('You must log in to view that page.')
            return redirect(url_for('login'))
    return wrapper


def is_authorized(fun):
    '''Checks whether a user is logged in and authorized to view a page.
    '''
    @wraps(fun)
    def wrapper(*args, **kwargs):
        user_email = flask_session.get('email')
        if user_email is not None:
            db_api = get_db_api()
            user = db_api.get_user_by_email(user_email)
            if user is not None:
                pantry_id = kwargs.get('pantry_id')
                assert pantry_id, "This function requires a pantry id."
                pantry = db_api.get_db_object_by_id('Pantry', pantry_id)
                if pantry in db_api.get_authorized_pantries(user):
                    kwargs['user'] = user
                    return fun(*args, **kwargs)
                else:
                    flash('You do not have access to that page.')
                    return redirect(url_for('pantry_index'))
            else:
                return abort(404)
        else:
            flash('You must log in to view that page.')
            return redirect(url_for('login'))
    return wrapper


@app.route(HOME)
def home():
    '''Reidirects to the home page, which is the pantry index page.
    '''
    return redirect(url_for('pantry_index'))

@app.route('/pantry/')
@is_logged_in
def pantry_index(user, **kwargs):
    '''Displays all pantrys for a given user.
    '''
    db_api = get_db_api()
    all_pantries = db_api.get_authorized_pantries(user)
    return render_template(P_INDEX_TMPLT,
                           pantries=all_pantries)

@app.route(ADD_PANTRY, methods=['GET', 'POST'])
@is_logged_in
def add_pantry(user, **kwargs):
    '''Create a new pantry.
    '''
    db_api = get_db_api()
    if request.method == 'POST':
        name = request.form['new_pantry_name']
        if name:
            duplicate = db_api.get_dbobject_by_name('Pantry', name, user.id)
            if duplicate:
                return render_template(P_ADD_TMPLT,
                                       form_error='You already have a pantry' \
                                       ' with that name.' \
                                       ' Please choose another.')
            db_api.add_object('Pantry', name, user.id)
            return redirect(url_for('pantry_index'))
        else:
            return render_template(P_ADD_TMPLT,
                                   form_error="The name can't be blank.")
    else:
        return render_template(P_ADD_TMPLT)


@app.route(DEL_PANTRY, methods=['GET', 'POST'])
@is_authorized
def del_pantry(user, pantry_id, **kwargs):
    '''Delete a pantry
    '''
    db_api = get_db_api()
    this_pantry = db_api.get_db_object_by_id('Pantry', user.id)
    all_categories = db_api.get_all_objects('Category', pantry_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db_api.del_object(this_pantry)
        return redirect(url_for('pantry_index'))
    else:
        return render_template(P_DEL_TMPLT,
                               pantry=this_pantry,
                               categories=all_categories)


@app.route(EDIT_PANTRY, methods=['GET', 'POST'])
@is_logged_in
def edit_pantry(user, pantry_id, **kwargs):
    '''Edit a pantry.
    '''
    db_api = get_db_api()
    this_pantry = db_api.get_db_object_by_id('Pantry', pantry_id)
    if request.method == 'POST':
        edited_name = request.form.get('updated_name')
        if edited_name:
            this_pantry.name = edited_name
            return redirect(url_for('pantry_index'))
        else:
            error = 'The pantry name cannot be blank.'
            return render_template(P_EDIT_TMPLT, pantry=this_pantry,
                                   form_error=error)
    else:
        return render_template(P_EDIT_TMPLT, pantry=this_pantry)


@app.route(PANTRY_JSON)
@is_logged_in
def get_pantries_json(user, **kwargs):
    '''Display JSON for this user's pantries. Does not display shared pantries.
    '''
    db_api = get_db_api()
    all_pantries = db_api.get_all_objects("Pantry", user.id)
    return jsonify(all_pantries=[pantry.serialize for pantry in all_pantries])


@app.route(PANTRY, methods=['GET', 'POST'])
@is_authorized
def category_index(pantry_id, **kwargs):
    '''Display the category index page.
    '''
    db_api = get_db_api()
    all_categories = db_api.get_all_objects('Category', pantry_id)
    return render_template(C_INDEX_TMPLT,
                           categories=all_categories,
                           pantry_id=pantry_id)

@app.route(ALL_CATEGORIES_JSON)
@is_authorized
def get_categories_json(pantry_id, **kwargs):
    '''Provides a JSON representation of the current categories in the pantry.
    '''
    db_api = get_db_api()
    all_categories = db_api.get_all_objects('Category', pantry_id)
    return jsonify(all_categories=[category.serialize for category
                                   in all_categories])
@app.route(CATEGORY)
@is_authorized
def display_category(pantry_id, category_id, **kwargs):
    '''Display individual category page.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    all_items = db_api.get_all_objects('Item', category_id)
    return render_template(C_DISP_TMPLT, category=this_category, items=all_items,
                           pantry_id=pantry_id)
@app.route(CATEGORY_JSON)
@is_authorized
def get_category_json(pantry_id, category_id, **kwargs):
    '''Return JSON for individual category.
    '''
    db_api = get_db_api()
    all_items = db_api.get_all_objects('Item', category_id)
    return jsonify(all_items=[item.serialize for item in all_items])

@app.route(EDIT_CATEGORY, methods=['GET', 'POST'])
@is_authorized
def edit_category(pantry_id, category_id, **kwargs):
    '''Edit a category entry.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    if request.method == "POST":
        if request.form["updated_name"]:
            this_category.name = request.form["updated_name"]
            return redirect(url_for("category_index", pantry_id=pantry_id))
        else:
            error = "You must type a new category name."
            return render_template(C_EDIT_TMPLT,
                                   category=this_category,
                                   form_error=error)
    else:
        return render_template(C_EDIT_TMPLT, category=this_category)

@app.route(DEL_CATEGORY, methods=['GET', 'POST'])
@is_authorized
def del_category(pantry_id, category_id, **kwargs):
    '''Delete a category.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    all_items = db_api.get_all_objects('Item', category_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db_api.del_object(this_category)
        return redirect(url_for('category_index', pantry_id=pantry_id))
    else:
        return render_template(C_DEL_TMPLT,
                               category=this_category,
                               items=all_items,
                               pantry_id=pantry_id)

@app.route('/pantry/<int:pantry_id>/category/add/', methods=['GET', 'POST'])
@is_authorized
def add_category(pantry_id, **kwargs):
    '''Add a category.
    '''
    db = get_db_api()
    if request.method == 'POST':
        name = request.form['new_category_name']
        if name:
            duplicate = db.get_dbobject_by_name('Category', name, pantry_id)
            if duplicate:
                return render_template(C_ADD_TMPLT,
                                       form_error="That category already" \
                                       + " exists.")
            db.add_object('Category', name, pantry_id)
            return redirect(url_for('category_index', pantry_id=pantry_id))
        else:
            return render_template(C_ADD_TMPLT,
                                   form_error="The name can't be blank!")
    else:
        return render_template(C_ADD_TMPLT)

@app.route(ITEM)
@is_authorized
def display_item(pantry_id, category_id, item_id, **kwargs):
    '''Display an item.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    this_item = db_api.get_db_object_by_id('Item', item_id)
    return render_template(I_DISP_TMPLT,
                           pantry_id=pantry_id,
                           category=this_category, item=this_item)

@app.route(ITEM_JSON)
@is_authorized
def get_item_json(pantry_id, category_id, item_id, **kwargs):
    '''Return JSON for individual item.
    '''
    db_api = get_db_api()
    this_item = db_api.get_db_object_by_id('Item', item_id)
    return jsonify(item_info=this_item.serialize)


@app.route(DEL_ITEM, methods=['GET', 'POST'])
@is_authorized
def del_item(pantry_id, category_id, item_id, **kwargs):
    '''Delete an item.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    this_item = db_api.get_db_object_by_id('Item', item_id)
    if request.method == 'POST' and request.form['confirm_del']:
        db_api.del_object(this_item)
        return redirect(url_for('display_category',
                                pantry_id=pantry_id, category_id=category_id))
    else:
        return render_template(I_DEL_TMPLT, pantry_id=pantry_id,
                               category=this_category, item=this_item)

@app.route(EDIT_ITEM, methods=['GET', 'POST'])
@is_authorized
def edit_item(pantry_id, category_id, item_id, **kwargs):
    '''Edit an item.
    '''
    db_api = get_db_api()
    this_category = db_api.get_db_object_by_id('Category', category_id)
    this_item = db_api.get_db_object_by_id('Item', item_id)
    if request.method == 'POST':
        if request.form['item_name']:
            this_item.name = request.form['item_name']
            this_item.quantity = request.form['quantity']
            this_item.price = request.form['price']
            this_item.description = request.form['description']
            return redirect(url_for('display_item', pantry_id=pantry_id,
                                    category_id=category_id, item_id=item_id))
        else:
            return render_template(I_EDIT_TMPLT,
                                   pantry_id=pantry_id,
                                   category=this_category,
                                   item=this_item,
                                   name_error="You must provide a name.")
    else:
        return render_template(I_EDIT_TMPLT,
                               pantry_id=pantry_id,
                               category=this_category,
                               item=this_item)

@app.route(ADD_ITEM, methods=['GET', 'POST'])
@is_authorized
def add_item(pantry_id, category_id, **kwargs):
    '''Add an item.
    '''
    if request.method == 'POST':
        if request.form["new_item_name"]:
            db_api = get_db_api()
            db_api.add_object('Item',
                         request.form["new_item_name"],
                         request.form["quantity"],
                         request.form["price"],
                         request.form["description"],
                         category_id)
            return redirect(url_for("display_category",
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

@app.route(LOGOUT, methods=['POST'])
def logout():
    if flask_session and flask_session.get('email'):
        del flask_session['access_token']
        del flask_session['gplus_id']
        del flask_session['username']
        del flask_session['email']
        del flask_session['picture']
        flash('you were logged out')
        return redirect(url_for('login'))
    else:
        flash('you were already logged out')
        return redirect(url_for('login'))

def build_json_response(msg, response_code):
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
    db_api = get_db_api()
    user = db_api.get_user_by_email(flask_session['email'])
    if user is not None:
        if user.name != flask_session['username']:
            user.name = flask_session['username']
    else:
        user = db_api.add_object('User', flask_session['username'],
                            flask_session['email'])


@app.route(GCONNECT, methods=['POST'])
def gconnect():
    '''Retrieve OAuth2 state token from client request and obtain 
    authorization code from Google.
    '''
    if request.args.get('state') != flask_session['state']:
        return build_json_response('Invalid state token for gConnect.', 401)
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
            return build_json_response('Failed to create credentials object' + \
                                      ' code.', 401)
        # validate access token
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token' + \
               '=%s' % access_token)
        http_client_instance = httplib2.Http()
        result = json.loads(http_client_instance.request(url, 'GET')[1])
        if result.get('error') is not None:
            return build_json_response(result.get('error'), 500)
        # Does token match this user?
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            return build_json_response('Token does not match user.', 401)
        # Does token match this application?
        elif result['issued_to'] != CLIENT_ID:
            return build_json_response('Token does not match application', 401)
        stored_access_token = flask_session.get('access_token')
        stored_gplus_id = flask_session.get('gplus_id')
        if (stored_access_token is not None) and (gplus_id == stored_gplus_id):
            return build_json_response('Current user is already logged in: %s' \
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
    '''Attempt to disconnect the application from the user's google account.
    If there is an access_token, will attempt to contact google servers,
    if this fails, the user will be prompted to clear cookies and log back in
    before attempting to disconnect because the access token may be stale.
    '''
    access_token = flask_session['access_token']
    print 'In fun gdisconnect, access token is %s' % access_token
    print 'Username is'
    print flask_session['username']
    if access_token is None:
        print 'No access token.'
        return build_json_response('Current user not connected.', 401)
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
        return redirect(url_for('login'))
    else:
        print 'failed to revoke token'
        return build_json_response('failed to revoke token', 400)


if __name__ == '__main__':
    app.debug = True
    app.run(port=5001)
