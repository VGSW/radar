FROM alpine
LABEL vendor=oftl

RUN apk update \
 && apk upgrade \
 && apk add \
    python3 \
    python3-dev \
    pytest \
    py-yaml

RUN mkdir /root/log/
RUN mkdir /root/sls/
COPY sls/ /root/sls/

WORKDIR /root/
CMD ["python3", "-m", "sls"]
