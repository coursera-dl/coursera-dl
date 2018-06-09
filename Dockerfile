FROM python:3.4-slim

LABEL maintainer "opsxcq@strm.sh"

WORKDIR /src
COPY requirements.txt /src

COPY requirements-dev.txt /src

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libssl-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt && \
    apt-get purge -y --auto-remove gcc g++ libssl-dev

COPY . /src
RUN python setup.py install

WORKDIR /courses
ENTRYPOINT ["coursera-dl"]
CMD ["--help"]
