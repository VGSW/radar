DOCKER=/usr/bin/docker
PYTEST=/usr/bin/pytest
FIND=/usr/bin/find
BASE=`pwd`

IMAGE=sls_dask
CONTAINER=sls_dask01

build:
	$(warning "make sure needed config files are available")
	${DOCKER} build --tag ${IMAGE} --file Dockerfile src/

run:
	${DOCKER} run --rm -it --volume ${BASE}/data:/root/data ${IMAGE}

inspect:
	${DOCKER} run --rm -it --volume ${BASE}/data:/root/data ${IMAGE} sh

clean:
	${FIND} . -name *pyc | xargs rm -f
	${FIND} . -name __pycache__ | xargs rm -rf
	${FIND} . -name .pytest_cache | xargs rm -fr

distclean: clean
	${DOCKER} rm ${CONTAINER}
	${DOCKER} rmi ${IMAGE}

test:
	${DOCKER} run --rm -it --volume ${BASE}/data:/root/data ${IMAGE} ${PYTEST} sls/
