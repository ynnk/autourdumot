(M) Autour Du Mot
=================

Get resources
-------------

Graphs dicosyn & jdm : sync hubic for latest graphs

Glaff 1.2.1:

    $ make get_glaff


Full install
------------

Install virtualenv and requirements :

    $ virtualenv --system-site-packages venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

Get cello_libjs dep:

    $ make link_libjs


Create index (~5 minutes on my laptop):

    $ export PYTHONPATH=./:$PYTHONPATH
    $ python index.py -i tmuse

it loads jdm & dicosyn graphs, computes proxemies and stores in elasticsearch

Run the app:

    $ python app/tmuse_es_app.py

Browse app: (only french verbs supported, ex 'causer'):

    $ firefox http://localhost:5000/causer


Run it using external ES
------------------------

You can use `ES_HOST` and `ES_INDEX` env variable to setup ES host and index:

    $ export ES_HOST=10.10.21.125
    $ export ES_HOST=tmuse_test
    $ python app/tmuse_es_app.py
