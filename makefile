#CELLO LibJS dep
LIBJS_DIR=./app/cello_libjs
LIBJS_ORIGIN=git@git.kodexlab.com:kodexlab/cellojs.git
LIBJS_VERSION=master

## This var may be overriden by var env
ES_HOST ?= "localhost:9200"
ES_INDEX ?= "autourdumot"
#ES_DOC_TYPE ?= "graph" #TODO make it configurable

#GRAPH_DIR=/work/hubic/Graphs/jdm/
GRAPH_DIR=./data_graphs/


.PHONY: get_libjs link_libjs python_dep index_graphs

all_dep: get_libjs python_dep

get_libjs:
	rm -rf ${LIBJS_DIR}
	git clone --no-checkout ${LIBJS_ORIGIN} ${LIBJS_DIR}
	cd ${LIBJS_DIR} && git checkout -f ${LIBJS_VERSION}
	cd ${LIBJS_DIR} && make build

link_libjs:
	rm -rf ${LIBJS_DIR}
	ln -s  ../../cello_libjs/ ${LIBJS_DIR}


python_dep:
	pip install -r requirements.txt

get_glaff:
	wget http://redac.univ-tlse2.fr/lexiques/glaff/GLAFF-1.2.1.tar.bz2  
	tar -xjf GLAFF-1.2.1.tar.bz2


check_index:
	echo "host: ${ES_HOST} idx: ${ES_INDEX}"

index_graphs:
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} -d
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.A.flat" --gpath "${GRAPH_DIR}fr.A.JDM-11012015-v1_666_777-e5-s_avg-flat.pickle" --gpos "A" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.V.flat" --gpath "${GRAPH_DIR}fr.V.JDM-11012015-v1_666_777-e5-s_avg-flat.pickle" --gpos "V" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.N.flat" --gpath "${GRAPH_DIR}fr.N.JDM-11012015-v1_666_777-e5-s_avg-flat.pickle" --gpos "N" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.E.flat" --gpath "${GRAPH_DIR}fr.E.JDM-11012015-v1_666_777-e5-s_avg-flat.pickle" --gpos "E" --glang "fr"

	
index_graphs-dev:
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.A.flat" --gpath "${GRAPH_DIR}fr.A.JDM.pickle" --gpos "A" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.V.flat" --gpath "${GRAPH_DIR}fr.V.JDM.pickle" --gpos "V" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.N.flat" --gpath "${GRAPH_DIR}fr.N.JDM.pickle" --gpos "N" --glang "fr"
	python index.py --host ${ES_HOST} --idx ${ES_INDEX} --gname "jdm.E.flat" --gpath "${GRAPH_DIR}fr.E.JDM.pickle" --gpos "E" --glang "fr"

test:
	py.test -v ./*.py --doctest-module
