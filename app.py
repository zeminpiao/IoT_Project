
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, send_from_directory, make_response, \
     send_file, current_app
import json
import re, os
import sys
import requests
import time

# create our little application :)
app = Flask(__name__)

# global variables
IP = 0
port  = 0
jsoncontent = 0
json_device = 0
flag_deployment = 1
Validation = 0
JSON_Ownership_Priority_NoUserID = 0
UPLOAD_FOLDER = '/home/yuefeng/Desktop/APPLICATION_BUILDR/download/'
content_send_timeinfo = {}
Primary_INFO = {}
runningtime_info = 0
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='/tmp/flaskr.db',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
    
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""showing the useraccount html page as well as the data in entries table, transfering the data into json"""
@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select UserID, Name, Email, username, Password, GroupNumber, RoomID from entries')
    entries = cur.fetchall()
    rows = [ dict(entry) for entry in entries ]
    print rows
    rows_json = json.dumps(rows)
    print rows_json
    #jsoned = json.dumps(entries)
    #print(entries)
    global jsoncontent
    jsoncontent = rows_json
    cur2 = db.execute('select LightID from Lights')
    entries2 = cur2.fetchall()
    
    return render_template('useraccount.html', entries=entries, entries2=entries2)

"""put new values to the entries table"""
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (UserID, Name, Email, username, Password, GroupNumber, RoomID, User1Position,User2Position,User3Position) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 [request.form['userid'], request.form['name'], request.form['email'], request.form['username'], request.form['pass'], request.form['groups'], request.form['RoomID'], request.form['user1position'], request.form['user2position'], request.form['user3position']])
    db.commit()
    #cur = db.execute('select UserID, Name, Email, username, Password, GroupNumber,User1Position,User2Position,User3Position from entries order by id desc')
    #entries = cur.fetchall()
    #print(entries)
    return redirect(url_for('show_entries'))

'''
@app.route('/identity')
def show_entries2():
    db = get_db()
    cur = db.execute('select * from light_primary')
    entries = cur.fetchall()
    cur2 = db.execute('select LightID from Lights')
    entries2 = cur2.fetchall()
    return render_template('idandbd.html', entries=entries, entries2=entries2)
'''
'''Input light information into database'''
@app.route('/add2', methods=['POST'])
def add_entry2():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into light_primary (LightID, Position, GroupNumber, RoomID)                  values (?, ?, ?, ?)',
                 [request.form['LightID'], request.form['Position'], request.form['GroupNumber'], request.form['RoomID']])
    db.commit()
    return redirect(url_for('show_entries2'))

'''@app.route('PostOwnershipJson')
def postownershipjson():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur_user = db.execute('')
'''
'''Showing the webpage of commissionning'''
@app.route('/commission')
def commission():
    return render_template('commission.html')


'''The functionality of mDNS-SD and acquiring lightID information from broker'''

@app.route('/operating')
def operating():
    cmd = "avahi-browse -rtp _http._tcp"
    '''From the response of command above, mining for the IP address of broker'''
    r = os.popen(cmd)  
    text = r.read()
    pat = "=;[\w-]+;[\w-]+;Broker6;Web Site;[\w-]+;[\w-]+.[\w-]+;([\.\d]+);[\d]+;"
    #pat = "=;[\w-]+;[\w-]+;[\w-]+;[\w-]+;[\w-]+;[\w-]+.[\w-]+;([\.\d]+);[\d]+;"
    global IP
    IP = re.findall(pat, text)[0]
    #deviceinfo = requests.get()
    '''Get light information from broker'''
    s = 'http://{name}:8088/light-init'
    deviceinfo = requests.get(s.format(name=IP))
    entries_device = deviceinfo.json()
    db = get_db()
    #db.execute('')
    pat2 = "Light-Device-([\d]+)-[\d]+"
    for record in entries_device:
        db.execute('INSERT INTO Lights (LightID) values (?)', [record['LightID']])
        '''Because the sensor part is not complete, hereby we generate SensorID information based on LightID information'''
        sensorid = re.findall(pat2,record['LightID'])[0]
        sensor_id = "Sensor-Device-{name2}-1"
        SensorID = sensor_id.format(name2=sensorid)
        sen = {'SensorID1':SensorID}
        db.execute('INSERT INTO Sensor (SensorID) values (?)', [sen['SensorID1']])
    db.commit()
    cur = db.execute('SELECT * from Sensor')
    entries = cur.fetchall()
    print(entries)
    return render_template('operating.html', IP=IP)

'''Automatically generate three user accounts when testing overall systems'''
@app.route('/testinput')
def testinput():
    db = get_db()
    db.execute('insert into entries (UserID, Name, Email, username, Password, GroupNumber, RoomID, User1Position,User2Position,User3Position) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 ['Office-Worker-25', 'Zemin Piao', 'pzm6391@hotmail.com', 'pzm6391', 'pwd', 25, 'RoomID-1', '(1.0,2.0)', '(1.0,3.0)', '(1.0,4.0)'])
    db.execute('insert into entries (UserID, Name, Email, username, Password, GroupNumber, RoomID, User1Position,User2Position,User3Position) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 ['Office-Worker-16', 'Lan Wang', 'dd@hotmail.com', 'ddnoemi', 'pwd', 16, 'RoomID-1', '(1.0,3.0)', '(1.0,2.0)', '(1.0,4.0)'])
    db.execute('insert into entries (UserID, Name, Email, username, Password, GroupNumber, RoomID, User1Position,User2Position,User3Position) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 ['Office-Worker-6', 'Yuefeng Wu', 'Yuefeng@hotmail.com', 'Yuefeng','pwd', 6, 'RoomID-1', '(1.0,4.0)', '(1.0,5.0)', '(1.0,2.0)'])
    db.commit()
    return render_template('commission.html')

'''@app.route('/test')
def test():    cmd = "avahi-browse -rtp _http._tcp"
    r = os.popen(cmd)  
    text = r.read()
    pat = "=;[\w-]+;[\w-]+;test;Web Site;[\w-]+;[\w-]+.[\w-]+;([\.\d]+);[\d]+;"
    global IP
    IP = re.findall(pat, text)[0]
    #deviceinfo = requests.get()
    s = 'http://{name}:8088/'
    deviceinfo = requests.get(s.format(name=IP))
    entries_device = deviceinfo.json()
    print(entries_device)
    db = get_db()
    for record in entries_device:
        db.execute('INSERT INTO entries (UserID, Name, Email, Password, GroupNumber,User1Position,User2Position,User3Position) values (?, ?, ?, ?, ?, ?, ?, ?)', [record['UserID'], record['Name'], record['Email'], record['Password'], record['GroupNumber'], record['User1Position'], record['User2Position'], record['User3Position']])
    db.commit()
    curs = db.execute("SELECT * FROM entries")
    entries = curs.fetchall()
    print entries
    return render_template('operating.html', IP=IP)

    cur = db.execute('select * from light_primary where devicetype GLOB \'light\' order by id desc')
    'OwnershipPriority': {'user_type':'', 'user_id':'','light_color':'','Low_light':'','user_location_x':'','user_location_y':''}
'''
'''Create ownership_priority_string for broker for the convenience of parsing JSON file by broker part'''
@app.route('/ownership_nouserid', methods=['GET'])
def ownership_nouserid():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    '''Get lightID and position information'''
    cur = db.execute('select * from light_primary order by id desc')
    entries_device = cur.fetchall()
    '''Generate a dict for json encoding'''
    device_rows = [ dict(entry) for entry in entries_device ]
    #print(device_rows)
    cur2 = db.execute('select UserID, User1Position, User2Position, User3Position from entries')
    entries_user = cur2.fetchall()
    user_rows = [ dict(entry) for entry in entries_user ]
    #OwnershipPriority = []
    send_to_broker = []
    #json_file = []
    '''Generating JSON format file with ownership Priority information'''
    '''Put all the LightID into the dict'''
    for device_row in device_rows:
        Model_ownership = {'LightID':'', 'LocationX': '', 'LocationY': '', 'OwnershipPriority':[]}
        Model_ownership['LightID'] = device_row['LightID']
        user_x = 0
        user_y = 0
        '''Parsing the string format (user_x,user_y) position information into float user_x and float user_y'''
        for i in range(0, len(device_row['Position'])):
            if device_row['Position'][i] == ',':
                user_x = device_row['Position'][1:i]
                user_y = device_row['Position'][i+1:len(device_row['Position'])-1]
        Model_ownership['LocationX'] = float(user_x)
        Model_ownership['LocationY'] = float(user_y)
        send_to_broker.append(Model_ownership)
    #print(send_to_broker)
    '''Based on user type, generate respective dict'''
    for device_row in device_rows:
        for user_row in user_rows:
            if user_row['User1Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        #immediate = []
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER1', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        #immediate.append(s)
                        entry['OwnershipPriority'].append(s)
                    
            elif user_row['User2Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        #immediate = []
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER2', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        #immediate.append(s)
                        entry['OwnershipPriority'].append(s)
                
            elif user_row['User3Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        #immediate = []
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER3', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        
                        entry['OwnershipPriority'].append(s)

    #send_content = json.dumps(send_to_broker)
    #print(send_content)
    #s = 'http://{name}:8088/ownership-priority-update'
    #r = requests.post(s.format(name=IP), data=send_content)
    
    #returnvalue = r.text
    #if returnvalue.find('OK') >= 0:
        #Validation = 1
    '''Generate JSON file for light device'''
    for entry in send_to_broker:
        s_path = '/home/yuefeng/Desktop/APPLICATION_BUILDR/download/{name}.json'
        filename = entry['LightID']
        with open(s_path.format(name=filename),'w') as f:
            f.write(json.dumps(entry['OwnershipPriority']))

    global JSON_Ownership_Priority_NoUserID
    JSON_Ownership_Priority_NoUserID = send_to_broker
    print JSON_Ownership_Priority_NoUserID
    return redirect(url_for('ownership'))
'''Generate ownership priority main JSON file sent to broker for deciding the ownership priority, including the ownershipPriority string generated from above function'''
@app.route('/ownership', methods=['GET'])
def ownership():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.execute('select * from light_primary order by id desc')
    entries_device = cur.fetchall()
    device_rows = [ dict(entry) for entry in entries_device ]
    #print(device_rows)
    cur2 = db.execute('select UserID, User1Position, User2Position, User3Position from entries')
    entries_user = cur2.fetchall()
    user_rows = [ dict(entry) for entry in entries_user ]
    #OwnershipPriority = []
    send_to_broker = []
    #send_to_device = {}
    json_uri = []
    for device_row in device_rows:
        
        Model_ownership = {'LightID':'', 'LocationX': '', 'LocationY': '', 'OwnershipPriorityString':'', 'OwnershipPriority':{}}
        for i in range(0, len(JSON_Ownership_Priority_NoUserID)):
            if JSON_Ownership_Priority_NoUserID[i]['LightID'] == device_row['LightID']:
                Model_ownership['OwnershipPriorityString'] = JSON_Ownership_Priority_NoUserID[i]
        Model_ownership['LightID'] = device_row['LightID']
        user_x = 0
        user_y = 0
        for i in range(0, len(device_row['Position'])):
            if device_row['Position'][i] == ',':
                user_x = device_row['Position'][1:i]
                user_y = device_row['Position'][i+1:len(device_row['Position'])-1]
        Model_ownership['LocationX'] = float(user_x)
        Model_ownership['LocationY'] = float(user_y)
        send_to_broker.append(Model_ownership)
    #print(send_to_broker)
    for device_row in device_rows:
        for user_row in user_rows:
            if user_row['User1Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        immediate = {user_row['UserID']:{}}
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER1', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        immediate[user_row['UserID']].update(s)
                        entry['OwnershipPriority'].update(immediate)
                    
            elif user_row['User2Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        immediate = {user_row['UserID']:{}}
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER2', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        immediate[user_row['UserID']].update(s)
                        entry['OwnershipPriority'].update(immediate)
                        
            elif user_row['User3Position'].find(device_row['Position']) >= 0:
                
                for entry in send_to_broker:
                    if entry['LightID'] == device_row['LightID']:
                        #entry['OwnershipPriority'].append(user_row['UserID'])
                        pat2 = "Light-Device-([\d]+)-[\d]+"
                        pat3 = "Office-Worker-([\d]+)"
                        sensorid = re.findall(pat3, user_row['UserID'])[0]
                        sensor_id = "Sensor-Device-{name2}-1"
                        SensorID = sensor_id.format(name2=sensorid)
                        sen = {'SensorID1': SensorID}
                        immediate = {user_row['UserID']:{}}
                        user_x = 0
                        user_y = 0
                        for i in range(0, len(user_row['User1Position'])):
                            if user_row['User1Position'][i] == ',':
                                user_x = user_row['User1Position'][1:i]
                                user_y = user_row['User1Position'][i+1:len(user_row['User1Position'])-1]
                        s = {'user_type':'USER3', 'user_id':user_row['UserID'],'sensor_id':sen['SensorID1'],'light_color':'(255,255,255)','low_light':False,'user_location_x':float(user_x),'user_location_y':float(user_y)}
                        immediate[user_row['UserID']].update(s)
                        entry['OwnershipPriority'].update(immediate)
    
    #send_to_device_file = json.dumps(send_to_device)
    """Transform the content into json format"""
    send_content = json.dumps(send_to_broker)
    #print(send_content)
    s = 'http://{name}:8088/ownership-priority-update'
    r = requests.post(s.format(name=IP), data=send_content)
    
    returnvalue = r.text
    if returnvalue.find('OK') >= 0:
        flash('BrokerOK')

    return redirect(url_for('jsonurlpost'))
'''
@app.route('/ownership', methods=['POST'])
def ownershipupdate():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into priority (locationX, locationY, user1, user21, user22, user31, user32, user33, user34, user35)                  values (?,?,?,?,?,?,?,?,?,?)',
                 [request.form['locationX'],request.form['locationY'],request.form['user1'],request.form['user21'],request.form['user22'],request.form['user31'],request.form['user32'],request.form['user33'],request.form['user34'],request.form['user35']])
    db.commit()
    return redirect(url_for('ownership'))
'''
"""send the url for light device to download the json ownershippriority file"""
@app.route('/jsonurlpost')
def jsonurlpost():
    db = get_db()
    cur = db.execute('select * from Lights')
    entries = cur.fetchall()
    '''user regular expression to find IP address about host running this app.py'''
    cmd = "ifconfig enp0s3"
    r = os.popen(cmd)
    text = r.read()
    pat = "inet ([\.\d]+)"
    brokeruri = 'http://{name}:8088/uri-ownership'
    MYIP = re.findall(pat, text)[0]
    s = []
    for entry in entries:
        string_uri = "http://{name}:5000/download/{name2}.json"
        dic = {'LightID':entry['LightID'],'Uri':string_uri.format(name=MYIP,name2=entry['LightID'])}
        s.append(dic)
    try:
        requests.post(brokeruri.format(name=IP), json=s)
    except:
        pass

    #if reque.text():
        #flash('JsonUrlPost Successful')
    return render_template('ownership.html')


'''Send the user account information to broker'''
@app.route('/jsonupdate')
def sendtojobs():
    if not session.get('logged_in'):
        abort(401)
    print(jsoncontent)
    s = 'http://{name}:8088/user-info-update'
    r = requests.post(s.format(name=IP), data=jsoncontent)
    returnvalue = r.text
    print(returnvalue)
    if returnvalue.find('OK') >= 0:
        print('Veryok')
    return render_template('jsonupdate.html')

'''Update the user account information and send to broker'''
@app.route('/maintenance')
def maintenanced():
    db = get_db()
    cur = db.execute('select UserID, Name, Email, username, Password, GroupNumber,User1Position,User2Position,User3Position from entries')
    entries = cur.fetchall()
    rows = [ dict(entry) for entry in entries ]
    rows_json = json.dumps(rows)
    #print rows_json
    #jsoned = json.dumps(entries)
    #print(entries)
    global jsoncontent
    jsoncontent = rows_json
    return render_template('maintenance.html', entries=entries)

@app.route('/maintenance', methods = ['POST'])
def maintenance():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
   
    db.execute('update entries set Name = ?, Email = ?, username = ?, Password = ?, GroupNumber = ?,User1Position = ?,User2Position = ?,User3Position = ? where UserID = ?', ( request.form['name'], request.form['email'], request.form['username'], request.form['pass'], request.form['groups'], request.form['user1position'], request.form['user2position'], request.form['user3position'], request.form['userid']))
    db.commit()
    #print(entries)
    return redirect(url_for('maintenanced'))
'''
@app.route('/takecontrol')
def takecontrol():
    return render_template('takecontrol.html')

@app.route('/takingcontrol', methods = ['POST'])
def takingcontrol():
    s = 'http://{name}:8088/uri-execute'
    control_string = request.form['triggerstring']
    r = requests.post(s.format(name=IP), data=control_string)
    return render_template('takingcontrol.html')
'''
'''Showing the light state of light device inquired by the building manager'''
@app.route('/state')
def state():
    db = get_db()
    curs = db.execute('select * from deviceinfo')
    entries = curs.fetchall()
    curs2 = db.execute('select * from SensorInfo')
    entries2 = curs2.fetchall()
    s = 'http://{name}:8088/update-state'
    r = requests.get(s.format(name=IP))
    #s2 = 'http://{name}:8088/update-sensor-state'
    #r2 = requests.get(s.format(name=IP))
    deviceupdateinfo = r.json()
    #sensorupdateinfo = r2.json()
    #print(sensorupdateinfo)
    #print(deviceupdateinfo)
    db = get_db()
    for record in deviceupdateinfo:
        db.execute('INSERT INTO deviceinfo (LightColor, LightID, LightState, UserID, UserType, LowLight) values (?,?,?,?,?,?)', [record['LightColor'], record['LightID'], record['LightState'], record['UserID'], record['UserType'], record['LowLight']])
    #for record2 in sensorupdateinfo:
       #db.execute('INSERT INTO SensorInfo (SensorState, SensorID) values (?,?)', [record2['SensorState'],record2['SensorID']])
    db.commit()
    return render_template('state.html', entries = entries, entries2 = entries2)
'''
@app.route('/state', methods=['POST'])
def updatestate():
    
    return redirect(url_for('state'))
#@app.route('sendjsontodevice')
'''

'''Centralize behavior(The broker may not implement this part)'''
@app.route('/centralize')
def centralize():
    global flag_deployment
    if flag_deployment == 1:
        flag_deployment = 0
        s = 'http://{name}:8088/mode-change'
        requests.post(s.format(name=IP), data = 'C')
    return render_template('centralize.html')
'''Distribute behavior(The broker may not implement this part)'''
@app.route('/distribute')
def distribute():
    global flag_deployment
    if flag_deployment == 0:
        flag_deployment = 1
        s = 'http://{name}:8088/mode-change'
        requests.post(s.format(name=IP), data = 'D')
    return render_template('distribute.html')
'''Get usage time of light device inquired by building manager'''
@app.route('/get-usage')
def getusageget():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.execute('select * from Lights')
    entry_Light = cur.fetchall()
    cur2 = db.execute('select * from Sensor')
    entry_Sensor = cur2.fetchall()

    global content_send_timeinfo

    global runningtime_info

    return render_template('getusage.html', entry_Light = entry_Light, entry_Sensor = entry_Sensor, entries2 = content_send_timeinfo, entries3 = runningtime_info)

@app.route('/get-usage', methods=['POST'])
def getusage():
    if not session.get('logged_in'):
        abort(401)
    
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    if start_time > end_time:
        abort(401)
    light_id = request.form['LightID']
    sensor_id = request.form['SensorID']
    global content_send_timeinfo
    if light_id == 'null':
        if sensor_id == 'null':
            abort(401)
        else: 
            content_send_timeinfo = {'SensorID':sensor_id,'StartTime':start_time, 'EndTime':end_time}
    elif sensor_id == 'null':
        content_send_timeinfo = {'LightID':light_id,'StartTime':start_time, 'EndTime':end_time}
    else:
        content_send_timeinfo = {'LightID':light_id,'SensorID':sensor_id,'StartTime':start_time, 'EndTime':end_time}
    return redirect(url_for('getusageget'))
'''Send the start time and end time and light ID information to broker, in order to get light state information'''
@app.route('/get-usage-send')
def getusagesend():

    s = 'http://{name}:8088/get-usage'
    global content_send_timeinfo
    print(content_send_timeinfo)
    r = requests.post(s.format(name=IP), json = content_send_timeinfo)


    global runningtime_info
    runningtime_info = r.json()
    print(runningtime_info)

    return redirect(url_for('getusageget'))

'''login and log out functionality'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return render_template('home.html')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

'''Send uri of executable python file to light device in order to have direct control for light'''
@app.route('/senduri')
def showsenduri():
    #time.sleep(1)
    db = get_db()
    cur = db.execute('select * from Lights')
    entries = cur.fetchall()
    return render_template('senduri.html', entries = entries)

@app.route('/senduri', methods = ['POST'])
def senduri():
    cmd = "ifconfig enp0s3"
    r = os.popen(cmd)  
    text = r.read()
    uri = 'http://{name}:5000/download/Rainbow.py'
    pat = "inet ([\.\d]+)"
    MYIP = re.findall(pat, text)[0]
    global Primary_INFO
    Primary_INFO = {'LightID':request.form['LightID'],'Uri':uri.format(name=MYIP)}
    
    return redirect(url_for('showsenduri'))

@app.route('/senturi')
def senturi():
    global Primary_INFO
    target = 'http://{name2}:8088/python-uri-update'
    try:
        requests.post(target.format(name2=IP), json = Primary_INFO)
    except:
        pass

    return render_template('senduri.html')
'''Enable for devices to downloadd file from this host'''
@app.route('/download/<path:filename>')
def downloader(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename,as_attachment=True)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0')


