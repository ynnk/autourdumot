(M) Autour Du Mot
=================

Get resources
-------------

Graphs dicosyn & jdm : sync hubic for latest graphs

[Glaff 1.2.1](http://redac.univ-tlse2.fr/lexiques/glaff.html):

```bash
$ make get_glaff
```

Full install
------------

Install and run ElasticSearch (you may do otherwise for a production env):

```bash
$ wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.0.0/elasticsearch-2.0.0.tar.gz
$ tar xvf elasticsearch-2.0.0.tar.gz
$ cd elasticsearch-2.0.0/
$ # then run it:
$ ./bin/elasticsearch
```

Install virtualenv and requirements :

```bash
$ virtualenv --system-site-packages venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

Get cello_libjs dep:

```bash
$ make link_libjs
```

Create index (~5 minutes on my laptop):

```bash
$ export PYTHONPATH=./:$PYTHONPATH
$ make index
```

it loads jdm & dicosyn graphs, computes proxemies and stores in elasticsearch

Run the app:

```bash
$ python app/autourdumot.py
```

Browse app: (only french verbs supported, ex 'causer'):

```bash
$ firefox http://localhost:5000/causer
```

Run it using external ES
------------------------

You can use `ES_HOST` and `ES_INDEX` env variable to setup ES host and index:

```bash
$ export ES_HOST=10.10.21.125
$ export ES_HOST=autourdumot_test
```

To activate debugging:

```bash
$ export APP_DEBUG=true
```


Install for prod
----------------

Clone the repository:

```bash
$ git clone git@git.kodexlab.com:kodexlab/autourdumot.git
$ cd autourdumot.git
```

Setup python virtualenv:

```bash
$ virtualenv --system-site-packages venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ pip install -I gunicorn   # Force local install for gunicorn
```

Get cellojs:

```bash
$ make get_libjs
```

Then:
* Make sure you have ES installed...
* configure a sh to run everything
* configure supervisor

