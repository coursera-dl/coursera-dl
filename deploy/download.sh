#!/bin/sh

COURSES=$*

if [ ! -e ~/courses ]; then
    mkdir ~/courses
fi

if groups | grep -q "docker" ; then
    docker run --rm --name coursera -v ~/courses:/courses:Z coursera-img \
               coursera-dl -n --path /courses $COURSES
else
    sudo docker run --rm --name coursera -v ~/courses:/courses:Z coursera-img \
                    coursera-dl -n --path /courses $COURSES
fi
