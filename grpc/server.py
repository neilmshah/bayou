from concurrent import futures

import grpc
import redis
from flask import Flask, request, jsonify, json, Response
from flask_restful import Resource, Api, reqparse, abort
from ast import literal_eval
import a_e_pb2
import a_e_pb2_grpc
import sys
import time
import yaml
import threading

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
writeLog = []

_redis_port = 6379
redisList = ""
primary = 0
iteration = 0

dummy_booking_date = {
    "username": "abc",
    "room_no" : "123",
    "booking_date" : "mm-dd-yyyy",
    "start_time": "15",
    "alternate1_booking_date" : "mm-dd-yyyy",
    "alternate1_start_time": "9",
    "alternate2_booking_date" : "mm-dd-yyyy",
    "alternate2_start_time": "9",
    "booking_status": "tentative",
    "id": "0",
    "timestamp": "10"
    }
#writeLog.append(dummy_booking_date)
r = redis.StrictRedis(host='localhost', port=_redis_port, db=0)

def yield_entries():
    if len(writeLog) > 0:
        for item in writeLog:
            #print(item)
            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                            username = item["username"],
                                            room_no = item["room_no"],
                                            b_date = item["booking_date"],
                                            b_time = item["start_time"],
                                            a1_date = item["alternate1_booking_date"],
                                            a1_time = item["alternate1_start_time"],
                                            timestamp = item["timestamp"],
                                            status = item["booking_status"])

def does_entry_exists(id):
    for item in writeLog:
        if item['id'] == id:
            return True
    return False

def checkbookingAE(booking_info):
    global writeLog
    bookingStat = 'CanBeDone'

    for i in range(0,len(writeLog)):
        eachBooking = writeLog[i]

        if(eachBooking["id"] == booking_info["id"]):
            #print("id match")
            bookingStat = 'AlreadyInList'
            break


        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] <= booking_info["timestamp"]) ): 
                print("start time of server list less")
                bookingStat = 'CannotBeDone'
                break
            if ((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] > booking_info["timestamp"]) and eachBooking['booking_status'] == 'tentative'):
                eachBooking['start_date'] = eachBooking["alternate1_booking_date"]
                eachBooking['start_time'] = eachBooking["alternate1_start_time"]
                eachBooking["alternate1_booking_date"] = ""
                eachBooking["alternate1_start_time"] = ""
                writeLog[i] = eachBooking #Overwrite the existing booking info with the new updated start_date/time
                #writeLog.append(eachBooking)

                #del writeLog[i]

    return bookingStat

def run_client(_connection_port):
    global writeLog
    #for i in range(0, 1):
    #    eachBooking = eval(r.hget('booking_info', i+1))
    #    writeLog.append(eachBooking)
    with grpc.insecure_channel('localhost:{}'.format(_connection_port)) as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        responses = stub.anti_entropy(yield_entries())
        for response in responses:
            print(response)

        print('$$$$$$$$$$$$$$$$$$$$$$$$$')
	
	

class BayouServer(a_e_pb2_grpc.BayouServicer):
    def __init__(self):
        global writeLog
        global _connection_ports
        threading.Thread(target=self.execute_anti_entropy, daemon=True).start()
        
    def execute_anti_entropy(self):
        while True:
        #anti-entropy time
            time.sleep(5)

            #print(_server_port)

            try:
                for connection_port in _connection_ports:
                    run_client(str(connection_port))
            except:
                print("no other server")

    def anti_entropy(self,request_iterator,context):
        global writeLog
        self.new_list = []
        for request in request_iterator:

            calendar_entry = {}

            calendar_entry["username"] = request.username
            calendar_entry["room_no"] = request.room_no
            calendar_entry["booking_date"] = request.b_date
            calendar_entry["start_time"] = request.b_time
            calendar_entry["alternate1_booking_date"] = request.a1_date
            calendar_entry["alternate1_start_time"] = request.a1_time
            calendar_entry["timestamp"] = request.timestamp
            calendar_entry["booking_status"] = request.status
            calendar_entry["id"] = request.messageid

            bookingStat = checkbookingAE(calendar_entry)
            print("i was called for my first booking preference")
            if bookingStat == 'AlreadyInList':
                continue
            elif bookingStat == 'CanBeDone': #called for first preferred timestamp
                self.new_list.append(calendar_entry)
            else: # check for alternate booking prefernce
                if calendar_entry["alternate1_booking_date"]!= "" and calendar_entry["alternate1_start_time"]!="":
                    calendar_entry["booking_date"] = calendar_entry["alternate1_booking_date"]
                    calendar_entry["start_time"] = calendar_entry["alternate1_start_time"]
                    calendar_entry["alternate1_booking_date"]= ""
                    calendar_entry["alternate1_start_time"] = ""
                    alternateBookingStat = checkbookingAE(calendar_entry) #called for first preferred timestamp
                    print("i was called for my alternate booking preference")
                    if alternateBookingStat == 'CanBeDone':
                        self.new_list.append(calendar_entry)
                    else:
                        calendar_entry["booking_status"] = 'shouldBeDeleted'
                        self.new_list.append(calendar_entry)
                else:
                    calendar_entry["booking_status"] = 'shouldBeDeleted'
                    self.new_list.append(calendar_entry)

        if primary == 1: #If it's a primary server then it has to take a final decision
            writeLog += self.new_list
            self.sortWriteLogs()

        #print("Response log")
        #for item in writeLog:
            #print(item["id"]+" "+item["booking_date"]+" "+item["start_time"])
        for item in writeLog:
            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                            username = item["username"],
                                            room_no = item["room_no"],
                                            b_date = item["booking_date"],
                                            b_time = item["start_time"],
                                            timestamp = item["timestamp"],
                                            status = item["booking_status"])
    def sortWriteLogs(self):
        global writeLog
        #writeLog += self.new_list
        writeLog.sort(key=lambda x:x['timestamp'])
        self.executeRequests()
    
    def executeRequests(self):
            for booking in writeLog:
                if booking['booking_status'] == 'tentative' or booking['booking_status'] == 'shouldBeDeleted':
                    returnStat = self.executeInDB(booking)
                    if returnStat == 'committed':
                        print('committed: ',booking)
                        #writeLog.index([booking])['booking_status'] = 'committed'
                    elif returnStat == 'deleted':
                        print('Deleted: ',booking)
                        #writeLog.index([booking])['booking_status'] = 'deleted'
                        #writeLog.remove(booking)
                    else:
                        print('Tentative: ',booking)
    
    def executeInDB(self, bookingRequest):
        global iteration
        global writeLog
        iteration += 1
        if bookingRequest['booking_status'] == 'shouldBeDeleted':
            idx = writeLog.index(bookingRequest)
            writeLog[idx]['booking_status'] = 'deleted'
            bookingRequest['booking_status'] = 'deleted'
            r.lpush(redisList,bookingRequest)
            return 'deleted'
        elif iteration == 4:
            iteration = 0
            idx = writeLog.index(bookingRequest)
            writeLog[idx]['booking_status'] = 'committed'
            bookingRequest['booking_status'] = 'committed'
            r.lpush(redisList,bookingRequest)
            return 'committed'
        return ''


def run_server(_server_port,_connection_ports,_rest_server):
    print('Ports: {}, {}, {}'.format(_server_port,_connection_ports,_rest_server))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:{}'.format(_server_port))
    server.start()
    try:
        threading.Thread(target=app.run(port=_rest_server, debug=True), args=(_rest_server, True), daemon=True).start()
    except:
        print('Rest server connection error: ',_rest_server)

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
	



# --------Rest-------------------
app = Flask(__name__)
api = Api(app)

id = 0


parser = reqparse.RequestParser()
parser.add_argument("booking_info")

def checkBooking(booking_info):
    global writeLog
    bookingAvail = True

    for i in range(0, r.llen(redisList)):
        eachBooking = literal_eval(r.lindex(redisList, i).decode('utf-8'))
        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if(eachBooking["start_time"]==booking_info["start_time"]):
                bookingAvail=False
                return bookingAvail
    for i in range(0,len(writeLog)):
        eachBooking = writeLog[i]
        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if(eachBooking["start_time"]==booking_info["start_time"]):
                bookingAvail=False
                return bookingAvail
    return bookingAvail

def bookRoom(booking_info):
    global writeLog
    print("wewewewewewewewewewewewewewewewe")
    print(writeLog)
    if(checkBooking(booking_info)):
        print('11 time checkBooking called')
        writeLog.append(booking_info)
        #r.lpush(redisList,booking_info)
        return True
    else:
        if(booking_info["alternate1_booking_date"]!="" and booking_info["alternate1_start_time"]!=""):
            booking_info["booking_date"]=booking_info["alternate1_booking_date"]
            booking_info["start_time"]=booking_info["alternate1_start_time"]
            booking_info["alternate1_booking_date"]=""
            booking_info["alternate1_start_time"]=""
            if(checkBooking(booking_info)):
                print('22 time checkBooking called')
                writeLog.append(booking_info)
                #r.lpush(redisList,booking_info)
                return True
            else:
                if(booking_info["alternate2_booking_date"]!="" and booking_info["alternate2_start_time"]!=""):
                    booking_info["booking_date"]=booking_info["alternate2_booking_date"]
                    booking_info["start_time"]=booking_info["alternate2_start_time"]
                    booking_info["alternate2_booking_date"]=""
                    booking_info["alternate2_start_time"]=""
                    if(checkBooking(booking_info)):
                        print('33 time checkBooking called')
                        writeLog.append(booking_info)
                        #r.lpush(redisList,booking_info)
                        return True
    return False

class BookRoom(Resource):
    def post(self):
        args = parser.parse_args()
        booking_info = literal_eval(args["booking_info"])
        global id
        id += 1
        booking_info["id"]=str(id)
        booking_info["timestamp"]=str(time.time())
        booking_info["booking_status"]="tentative"
        print(booking_info)
        if(bookRoom(booking_info)): return 'Tentatively booked primary or alternate slot.',201
        else: return 'Booking slots unavailable.', 304

class GetBooking(Resource):

	def get(self, username):
		users_bookings = dict()
		user_booking_list_item = []
		for i in range(0, r.llen(redisList)):
			users_bookings_item = {}
			eachBooking = literal_eval(r.lindex(redisList, i).decode('utf-8'))
			if eachBooking["username"] == username:
				users_bookings_item["room_no"] = eachBooking["room_no"]
				users_bookings_item["booking_date"] = eachBooking["booking_date"]
				users_bookings_item["start_time"] = eachBooking["start_time"]
				users_bookings_item["booking_status"] = eachBooking["booking_status"]

				user_booking_list_item.append(users_bookings_item)

		users_bookings[username] = user_booking_list_item
		js = json.dumps(users_bookings)
		resp = Response(js, status=200, mimetype='application/json')
		print("Response from server is {}" .format(resp))

		return resp

api.add_resource(GetBooking, '/booking/<string:username>')
api.add_resource(BookRoom, '/booking')


# ----------------------Main--------------------
if __name__ == '__main__':
    config_dict = yaml.load(open('config.yaml'))

    config_dict = config_dict[str(sys.argv[1])]

    _server_port = str(config_dict['server_port'])
    _connection_ports = config_dict['connection_port']
    _rest_server_port = config_dict['rest_server_port']

    primary = config_dict['primary']
    redisList = "bookings" + str(_server_port)
    run_server(_server_port,_connection_ports, _rest_server_port)

#app.run(port=_server_port, debug=True)
