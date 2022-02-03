#!/bin/sh

export $(cat /config.env | xargs)
exec $@