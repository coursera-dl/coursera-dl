FROM ubuntu:14.04
MAINTAINER Dmitry Senin <seninds@gmail.com>

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y git build-essential libssl-dev libffi-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-dev
RUN pip install ndg-httpsclient

COPY .netrc /root/.netrc
RUN chmod 0600 /root/.netrc

RUN cd /root && git clone https://github.com/coursera-dl/coursera.git
RUN cd /root/coursera && pip install -r requirements.txt
RUN cd /usr/bin && ln -s /root/coursera/coursera-dl coursera-dl
