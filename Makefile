DOCKER=/usr/bin/docker
PYTEST=/usr/bin/pytest
FIND=/usr/bin/find
BASE=`pwd`

IMAGE=sls
CONTAINER=sls01

build:
	$(warning "make sure needed config files are available")
	${DOCKER} build --tag ${IMAGE} --file Dockerfile .

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
	${DOCKER} run --rm -it --volume ${BASE}/data:/root/data ${IMAGE} ${PYTEST} src/sls/

# setup config file by symlinking for test and clean up afterwards
local-test:
	cd src/sls && ln -s sls.yml-local sls.yml && cd ../../
	pytest
	rm src/sls/sls.yml
