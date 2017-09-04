Kitchen Pantry App
Track your food so things don't get lost in your pantry.
=============
To run this application (TLDR):
(1) Install the dependencies. Clone or download this repository.
(2) Create the local database.
(3) Run item_server.py.
(4) Navigate to localhost:5001.

Dependencies:
-------------
*Install these first.*
Python 2.7 -
http://python.org

Flask -
http://flask.pocoo.org/ (version 0.12.2)

SQLAlchemy -
http://www.sqlalchemy.org/ (version 1.1)

Google OAuth2 Python Client API -
https://developers.google.com/api-client-library/python/start/installation
(version 1.6.3)

Important Notes:
----------------
By default application is set to debug mode. Turn this off in production.

*Do not run this application in production without turning off the testing
features.*

The test server runs on port 5001.

Creating the Local Database:
----------------------------
If running for the first time on a local machine, navigate to directory where
files located, run python shell, import catalog_database_setup, run createDB(),
making sure the testing flag is False (it is by default).
