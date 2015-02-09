#CELLO LibJS dep
LIBJS_DIR=./app/cello_libjs
LIBJS_ORIGIN=ssh://192.168.122.99/var-hdd/git/cello_libjs/
LIBJS_VERSION=semui

.PHONY: get_libjs link_libjs python_dep

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

test:
	py.test -v ./*.py --doctest-module
