drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  UserID text not null,
  Name text not null,
  Email text not null,
  username text,
  Password text not null,
  GroupNumber integer,
  RoomID text not null,
  User1Position text not null,
  User2Position text not null,
  User3Position text not null
);

drop table if exists light_primary;
create table light_primary (
  id integer primary key autoincrement,
  LightID integer,
  Position text,
  GroupNumber integer,
  RoomID integer
);
  

drop table if exists Lights;
create table Lights (
  id integer primary key autoincrement,
  LightID text
);

drop table if exists Sensor;
create table Sensor (
  id integer primary key autoincrement,
  SensorID text
);

drop table if exists SensorInfo;
create table SensorInfo (
  SensorState text,
  SensorID text
);


drop table if exists OwnershipPriority;
create table OwnershipPriority (
  LightID text not null,
  user_type text not null,
  user_id text not null,
  light_color text not null,
  low_light text not null,
  user_location_x integer not null,
  user_location_y integer not null
);
  
drop table if exists usageinfo;
create table usageinfo (
  LightID text,
  SensorID text,
  start_time integer not null,
  end_time integer not null
);

drop table if exists deviceinfo;
create table deviceinfo (
  id integer primary key autoincrement,
  LightColor text not null,
  LightID text not null,
  LightState text not null,
  UserType text not null,
  UserID text not null,
  LowLight text not null
);
