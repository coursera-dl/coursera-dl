FROM python:3.6-slim

LABEL maintainer "https://github.com/coursera-dl/"

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libssl-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get purge -y --auto-remove gcc g++ libssl-dev

ARG VERSION
RUN pip install coursera-dl==$VERSION

WORKDIR /courses
ENTRYPOINT ["coursera-dl"]
CMD ["--help"]
