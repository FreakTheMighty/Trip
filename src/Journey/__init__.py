from xml.dom.minidom import parse
import datetime
import itertools
import math
import time

import geolocator.gislib as gislib
import numpy

class Path(object):

    def __init__(self, events=None):
        self.events = events or []
        for event in self.events:
            event.path = self

    def toJson(self):
        """
        Converts this `Path` object into valid json data.

        :rtype: dictionary
        """
        data = {"events":[]}
        for event in self.events:
            data['events'].append(event.toJson())
        data['info'] = {'traveled':self.distance()}
        return data

    @classmethod
    def fromJson(cls, data):
        """
        Factor method for creating a `Path` object from google latitude json data

        :param data: Google latitude json data
        :type data: dictionary
        """
        path = cls()
        for location in data['data']['items']:
            latlong = location['latitude'], location['longitude']
            epoch = int(location['timestampMs'])/1000.0
            path.createEvent(epoch,latlong,location.get('accuracy'))
        path.events.reverse()
        return path

    @classmethod
    def fromKml(cls, kmlFile):
        """
        Factory method for creating a `Path` object from a kml file.

        :param kmlFile: A file descriptor pointing to a kml file
        :type kmlFile: File
        """
        path = cls()
        dom = parse(kmlFile)
        whenwhere = zip(dom.getElementsByTagName("when"),dom.getElementsByTagName("gx:coord"))
        whenwhere = [(w.firstChild.nodeValue, wh.firstChild.nodeValue) for w,wh in whenwhere]
        for when, where in whenwhere:
            date, time_rec = when.split("T")
            year,month,day = date.split("-")
            hour, minute, second = time_rec.split(":")[:3]
            second = second.split("-")[0]
            timeObj = datetime.datetime(int(year),int(month),int(day),
                                        int(hour),int(minute))
            lat, lng, wha = where.split()
            lat = float(lat)
            lng = float(lng)
            path.createEvent(time.mktime(timeObj.timetuple()),(lat,lng),None)
        return path


    def samplePath(self, ctime, sampleCnt, spacing):
        """
        Returns a window of n sample centered around ctime.

        :param ctime: The center of sample window given in seconds since the epoch
        :type ctime: float

        :param sampleCnt: Number of surounding samples.
        :type sampleCnt: int

        :param spacing: Spacing of samples in seconds
        :type spacing: float
        """
        pathSamples =[]
        start = ctime - spacing * (sampleCnt/2)
        end = ctime + spacing * (sampleCnt/2)
        step = (end - start)/spacing
        samples = list(numpy.arange(start,end,step))
        for sample in samples:
            pathSamples.append(self.atTime(sample,True))
        return pathSamples

    def start(self):
        """
        :returns: First event in path.
        :rtype: `Event`
        """
        return self.events[0]

    def end(self):
        """
        :returns: Last event in path.
        :rtype: `Event`
        """
        return self.events[-1]

    def createEvent(self, epoch, location, accuracy=None):
        """
        Creates an event at the given time and location.

        :param epoch: Time in seconds since the epoch
        :type epoch: float

        :param location: Latitude and Longitude in the form (lat,lng)
        :type location: tuple
        """
        event = Event(epoch,location,accuracy)
        event.path = self
        self.events.append(event)

    def appendEvent(self, event):
        """
        Appends the provided event and sets its path to this path

        :param event: Event to append
        :type event: `Event`
        """
        event.path = self
        self.events.append(event)

    def insertEvent(self, idx, event):
        """
        Insert the event at the given index and set its path to this path.

        :type idx: int
        :type event: `Event`
        """
        event.path = self
        self.events.insert(idx,event)

    def sort(self):
        """
        Sorts the events by the time at which they were recorded.
        """
        self.events.sort(key=lambda e: e.epoch)

    def averageSpeed(self):
        return sum([e.speed() for e in self.events])/len(self.events)

    def interpolate(self,resolution=60.0):
        """
        Performs linear interpolation of the current path.

        :param resolution: The sample size in seconds
        :type resolution: float

        :returns: A new `Path`
        :rtype: `Path`
        """
        self.sort()
        start = self.events[0].epoch
        end = self.events[-1].epoch
        times = numpy.arange(start,end,resolution)
        newEvents = Path()
        for t in times:
            newEvents.appendEvent(self.atTime(t))
        return newEvents

    def atTime(self, epoch, insert=False):
        """
        Returns an `Event` object at the specified epoch by interpolating
        nearest samplings.

        :param epoch: Sample time
        :type epoch: float

        :param insert: Flag to indicate whether event should be inserted into current path
        :type insert: boolean
        """

        before = None
        after = None

        if epoch < self.events[0].epoch:
            before = self.events[0]
            after = self.events[1]

        elif epoch > self.events[-1].epoch:
            before = self.events[-2]
            after = self.events[-1]

        else:
            for idx, event in enumerate(self.events):
                if event.epoch > epoch:
                    after = event
                    before = self.events[idx-1]
                    if tuple(after.location) != tuple(before.location):
                        break

        t3l = epoch - before.epoch
        t2l = after.epoch - before.epoch
        mag = t3l/t2l

        newEvent = Event(epoch,
                    ((after.location[0]-before.location[0])*mag + before.location[0],
                    ((after.location[1]-before.location[1])*mag)+ before.location[1]))

        if insert:
            self.appendEvent(newEvent)
            self.sort()
            return newEvent
        else:
            return newEvent

    def duration(self):
        """
        :returns: Time in seconds between the first event in the path and last event
        :rtype: float
        """
        delta = self.end().epoch - self.start().epoch
        return delta

    def distanceTraveled(self):
        """
        :returns: Total distance traveled along path in kilometers
        :rtype: float

        .. note:
            This requires additional work to handle noise from indoor readings.
        """
        self.sort()
        total = 0
        for idx, event in enumerate(self.events[:-1]):
            total += gislib.getDistance(event.location, self.events[idx+1].location)
        return total

    def distance(self):
        """
        :returns: Distance between first and last 
        :rtype: float
        """
        self.sort()
        return gislib.getDistance(self.start().location,self.end().location)

class Event(object):

    def __init__(self,epoch,location,accuracy=None):
        """
        The `Event` object represent a gps measurement.

        :param epoch: Time in epochal seconds of the measurment.
        :type epoch: float

        :param location: Location in the form (lat,lng)
        :type location: tuple (float, float)
        """

        self.path = None
        self.epoch = epoch
        self.location = location
        self.accuracy = accuracy

    def __repr__(self):
        return "< %s :: %s> at %s" % (self.epoch,self.location, id(self))

    def toJson(self):
        return {"date":self.epoch,"location":self.location}

    def neighbor(self, relative):
        idx = self.path.events.index(self)
        idx += relative
        return self.path.events[idx]

    def distanceTo(self, event):
        return gislib.getDistance(event.location, self.location)

    def timeNear(self, dist):
        """
        Returns the amount of time spent near this point by comparing surrounding
        points on the path.

        :param dist: Threshold for defining what points should be considered near.
                     Specified in kilometers.
        :type dist: float
        """
        idx = self.path.events.index(self)
        nearEvents = []
        if idx != 0:
            for event in self.path.events[::-1][-idx:]:
                if self.distanceTo(event) < dist:
                    nearEvents.append(event)
                else:
                    break
                nearEvents.reverse()

        for event in self.path.events[idx:]:
            if self.distanceTo(event) < dist:
                nearEvents.append(event)
            else:
                break

        if len(nearEvents) > 1:
            return nearEvents[-1].epoch-nearEvents[0].epoch
        else:
            return 0

    def heading(self,event=None):
        """
        Heading of the current event relative to either the next
        event or a specified event.

        :param event: Event to calculate heading against.
        :type event: `Event`

        :rtype: float
        """
        if event is None:
            next_event = self.neighbor(1)
        else:
            next_event = event
        lon1,lat1 = self.location
        lon2,lat2 = next_event.location
        tc1=math.atan2(math.sin(lon2-lon1)*math.cos(lat2),
           math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1))%2*math.pi
        tc1 = tc1*180/math.pi
        return tc1

    def speed(self,relative=-1):
        """
        Calculates the speed of the current event by comparing 
        its position with its relative.  Defaults to looking at the previous event.

        :returns: Kilometers per hour
        :rtype: float
        """

        previous = self.neighbor(relative)
        deltaTime = self.epoch - previous.epoch
        divisor = deltaTime/3600.0
        distance = gislib.getDistance(previous.location,self.location)
        if divisor == 0:
            return 0
        else:
            return distance / divisor

    def toDateTime(self):
        """
        Convenience function for going from epochal seconds to date time object.

        :rtype: DateTime
        """
        return datetime.datetime.fromtimestamp(self.epoch)


def segmentTrips(path):
    """
    Given a path attempt to segment it into paths representing periods
    of movement and stillness.

    :param path: A `Path` object containing events.  Typically these are measurements
                 throughout a day.
    :type path: `Path`

    :returns: A list of `Path` objects where each path object is either a trip, or location
              where the measures stayed stationary.
    :rtype: list<`Path`>
    """

    # Calculate the time spent at each event
    timeat = [e.timeNear(.1) for e in path.events]

    # Using itertools group them by contiguous events with similar amounts of
    # time spent at those events.  Currently events are rounded to the nearest
    # 1000 seconds.
    groups = []
    uniquekeys = []
    for k, g in itertools.groupby(timeat, lambda i: math.floor(i/1000)*1000):
        groups.append(list(g))
        uniquekeys.append(k)

    # From the groupings, extract the corresponding Events
    eventGroups = []
    idx = 0
    for group in groups:
        pathSeg = []
        for m in group:
            pathSeg.append(path.events[idx])
            idx += 1
        eventGroups.append(pathSeg)

    # Pack the grouped events into Path objects
    paths = []
    for g in eventGroups:
        p = Path(g)
        paths.append(p)

    return paths
