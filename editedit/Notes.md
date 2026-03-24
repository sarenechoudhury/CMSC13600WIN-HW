Oxford English Dictionary definition of boilerplate (n) 3.  standardized pieces of text for use as clauses in contracts or as part of a computer program.  "some sections have been written as boilerplate for use in all proposals"


What are all these files for?

./editedit
./editedit/asgi.py                 # server service code
./editedit/__init__.py
./editedit/settings.py             # top-level "project" settings 
./editedit/urls.py                 # top-level urls.py, includes app/urls.py
./editedit/wsgi.py                 # server service code
./app
./app/migrations
./app/migrations/__init__.py       
./app/migrations/0001_initial.py   # internal-to-django, data on DDL
./app/models.py                    # Your DDL definitions
./app/__init__.py
./app/urls.py                      # Your code to specify which endpoints
./app/views.py                     # Your code to talk to server, db
./db.sqlite3                       # binary storing user table + app data
./manage.py                        # Django main control script (along with django-admin)

The __init__.py files allow python to include subdirectories and files within subdirectories using "import" statements. 




