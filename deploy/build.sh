#!/bin/sh

if groups | grep -q "docker" ; then
    docker build --tag coursera-img --rm .
else
    sudo docker build --tag coursera-img --rm .
fi
