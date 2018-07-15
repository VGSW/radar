FROM alpine
LABEL vendor=oftl

RUN apk update \
 && apk upgrade \
 && apk add \
    python3 \
    python3-dev \
    pytest \
    py-yaml \
    gcc \
    # limits.h
    musl-dev \
    linux-headers

RUN pip3 install \
    dask[distributed] \
    bokeh

RUN mkdir /root/log/
RUN mkdir /root/sls/
COPY sls/ /root/sls/

WORKDIR /root/
CMD ["python3", "-m", "sls"]
