library Trip;

import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';

class Trip {
  List<TEvent> events;
  num distance;
  
  Trip.fromJson(Map json) {
    events = new List();
    for (Map e in json['events']){
      TEvent event = new TEvent.fromJson(e);
      events.add(event);
      event.path = this;
    }
    distance = json['info']['traveled'];
  }
  
  DateTime get startDate  => events.first.date;
  String get startTimeFormatted => new DateFormat("Hm", "en_US").format(startDate);

  Duration get duration => events.last.date.difference(events.first.date);
}

class TEvent {
  
  num lat;
  num lng;
  DateTime date;
  Trip path;
  
  TEvent.fromJson(Map json) {
    lat = json['location'][0];
    lng = json['location'][1];
    num epoch = json['date']*1000.0;
    date = new DateTime.fromMillisecondsSinceEpoch(epoch.toInt());
  }
  
}

