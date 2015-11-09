(M) Autour Du Mot
=================

Get resources
-------------

Graphs dicosyn & jdm : sync hubic for latest graphs

Glaff 1.2.1:

    $ make get_glaff


install
--------

Install virtualenv and requirements :

    $ virtualenv --system-site-packages venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

Get cello_libjs dep:

    $ make link_libjs


Create index (~5 minutes on my laptop):

    $ python index.py -i tmuse

it loads jdm & dicosyn graphs, computes proxemies and stores in elasticsearch

Run the app:

    $ python app/tmuse_es_app.py

Note that you need to first edit index name in `tmuse_es_app.py` if you changed the index name default is 'tmuse'.

Browse app: (only french verbs supported, ex 'causer'):

    $ firefox http://localhost:5000/causer



   