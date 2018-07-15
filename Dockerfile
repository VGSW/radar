FROM alpine
LABEL vendor=oftl

RUN apk update \
 && apk upgrade \
 && apk add \
    python3 \
    python3-dev \
    pytest \
    py-yaml

RUN mkdir -p /root/src/sls/
COPY src/sls/sls.yml-container /etc/sls.yml
COPY . /root/src/sls/

RUN cd /root/src/sls && python3 setup.py install

WORKDIR /root/
CMD ["python3", "-m", "sls"]
