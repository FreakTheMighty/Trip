import 'dart:html';
import 'package:web_ui/web_ui.dart';
import 'package:google_oauth2_client/google_oauth2_browser.dart';
import 'dart:json' as JSON;
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';

import 'Trip.dart';

final clientid = '<your client id here>';
final locationQuery = 'https://www.googleapis.com/latitude/v1/location';

final Element queryButton = query("#query");
final ImageElement loginButton = query("#login");
final Element logoutButton = query("#logout");
final DateInputElement dateQueryInput = query("#dateQueryInput");

@observable DateTime dateQuery = new DateTime.now();
get queryDateFormatted => new DateFormat("E", "en_US").format(dateQuery);

List<Trip> trips = toObservable(new List());
/*TODO: Report bug, the second observable seems to be required
 * to make the trips observable trigger web_ui updates.
 */
@observable String status="";
@observable String overview="Your Trips";

final auth = new GoogleOAuth2(
    clientid,
    ["https://www.googleapis.com/auth/latitude.all.best"],
    tokenLoaded:oauthReady,
    autoLogin: false);


void oauthReady(Token token) {
  
  var testOAuth = new SimpleOAuth2(token.data);
  
  loginButton.style.display = "none";
  logoutButton.style.display = "inline-block";
  
  var request = new HttpRequest();
  final url = "https://www.googleapis.com/latitude/v1/location";
  
  request.onLoadEnd.listen((Event e) {
    if (request.status == 200) {
      var data = JSON.parse(request.responseText);
    }
  });
  
  request.open("GET", url);
  testOAuth.authenticate(request).then((request) => request.send());
}

void tripsFound(Map data){
  trips.clear();
  for (Map t in data['trips']){
    Trip trip = new Trip.fromJson(t);
    trips.add(trip);
  }
}

void tripsNotFound(var data){
  status = "No trips found.";
}

queryTrips(var event) {
  var start = new DateTime(dateQuery.year, dateQuery.month, dateQuery.day, 5);
  var end = start.add(const Duration(hours: 16));
  
  var request = new HttpRequest();
  var postrequest = new HttpRequest();
  postrequest.onLoadEnd.listen((Event e) {
    if (postrequest.status == 200) {
      tripsFound(JSON.parse(postrequest.responseText));
    } else {
      tripsNotFound("Error ${postrequest.status}: ${postrequest.statusText}");
    }
  });

  request.onLoadEnd.listen((Event e) {
    if (request.status == 200) {
      var data = JSON.parse(request.responseText);
      if (data['data'].containsKey("items")){
        postrequest.open("POST", "../trips");
        postrequest.setRequestHeader('content-type', 'application/json');
        postrequest.send(request.responseText); // perform the async POST
        status = " ";
      } else {
        status = "No location info was found for this date.";
        trips.clear();
      }
    }
  });
  
  if (auth.token != null){
    var url = "${locationQuery}?granularity=best&max-results=1000&min-time=${start.millisecondsSinceEpoch}&max-time=${end.millisecondsSinceEpoch}&access_token=${auth.token.data}";
    request.open("GET", url);
    request.send();
  } else {
    status = "Please login.";
  }
}


void main() {
  dateQuery = new DateTime.now();
  loginButton.onClick.listen((e){
    auth.login();
    status = "";
  });
  logoutButton.onClick.listen((e) {
                                    auth.logout();
                                    loginButton.style.display = "inline-block";
                                    logoutButton.style.display = "none";
                                  });
  
  queryButton.onClick.listen(queryTrips);
  
  loginButton.onMouseOver.listen((e){
    loginButton.src = "../assets/White-signin_Long_hover_44dp.png";
  });
  
  loginButton.onClick.listen((e){
    loginButton.src = "../assets/White-signin_Long_hover_44dp.png";
  });
  
  loginButton.onMouseOut.listen((e){
    loginButton.src = "../assets/White-signin_Long_base_44dp.png";
  });
  
  dateQueryInput.onChange.listen((e){
    print("Triggered");
    print(dateQuery);
    trips.clear();
  });
}
