Trip
====

This is a project I started after getting a scooter. I wanted a way to review 
the length of my commutes to see how they compared with other ways of commutting,
like taking the bus, the car or hitch hiking.

Google Latitude
---------------
Trip uses OAuth to access the user's Google Latitude data.  After granting access to
the client, location data for the day is retrieved, sent to the server, segmented and sent
back to the client for display.

Web UI
------
The client side is written in Dart, a client side language from Google. It uses the
Web UI library for the data driven UI.
