#!/usr/bin/env python2.6

import os
from bottle import route, run, static_file, post, request
import Journey

filepath   = os.path.realpath(os.path.dirname(__file__))
staticroot = os.path.realpath(os.path.join(filepath,"../src/TripClient/web"))

@post('/trips')
def listTrips():
    """
    Given latitude data segment the data into trips
    """
    path = Journey.Path.fromJson(request.json)
    segtrips = Journey.segmentTrips(path)
    segtrips = filter(lambda t: t.distance() > .1, segtrips)
    return {"trips":[t.toJson() for t in segtrips]}

@route('/<path:path>')
def static(path):
    return static_file(path,root=staticroot)

run(host='localhost', port=12357)
