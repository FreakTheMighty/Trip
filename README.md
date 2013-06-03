Trip
====

This is a project I started after getting a scooter. I wanted a way to review 
the length of my commutes to see how they compared with to other ways of commutting,
taking the bus, the car or say hitch hiking.

Google Latitude
---------------
Trip uses OAuth to access the user's Google Latitude data.  After granting access to
the client location data for the day is retrieved, set to the server, segmented and sent
back to the client for display.

Web UI
------
The client side is written in Dart, a javascript killer from Google. It uses the
Web UI library, also from google, for data driven UI.
