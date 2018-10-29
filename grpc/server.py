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

r = redis.StrictRedis(host='localhost', port=_redis_port, db=0)

def yield_entries():
    global writeLog
    if len(writeLog) > 0:
        for i in range(0,len(writeLog)):
            item = writeLog[i]
            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                            username = item["username"],
                                            room_no = item["room_no"],
                                            b_date = item["booking_date"],
                                            b_time = item["start_time"],
                                            a1_date = item["alternate1_booking_date"],
                                            a1_time = item["alternate1_start_time"],
                                            a2_date = item["alternate2_booking_date"],
                                            a2_time = item["alternate2_start_time"],
                                            timestamp = item["timestamp"],
                                            status = item["booking_status"])

def does_entry_exists(id):
    global writeLog
    for item in writeLog:
        if item['id'] == id:
            return True
    return False

def checkbookingAE(booking_info):
    if(does_entry_exists(booking_info['id'])):
        return 'AlreadyInList'
    global writeLog
    bookingStat = 'CanBeDone'
    if len(writeLog)>0:
        for i in range(0,len(writeLog)):
            eachBooking = writeLog[i]

            if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"] and eachBooking["start_time"] == booking_info["start_time"]):
                if((eachBooking["timestamp"] <= booking_info["timestamp"]) ): 
                    print("start time of server list less")
                    bookingStat = 'CannotBeDone'
                    break
                elif ((eachBooking["timestamp"] > booking_info["timestamp"]) and eachBooking['booking_status'] == 'tentative'):
                    eachBooking['start_date'] = eachBooking["alternate1_booking_date"]
                    eachBooking['start_time'] = eachBooking["alternate1_start_time"]
                    eachBooking["alternate1_booking_date"] = ""
                    eachBooking["alternate1_start_time"] = ""
                    writeLog[i] = eachBooking
                    break

    return bookingStat

def make_new_object(request):
        calendar_entry = {}
        calendar_entry["username"] = request.username
        calendar_entry["room_no"] = request.room_no
        calendar_entry["booking_date"] = request.b_date
        calendar_entry["start_time"] = request.b_time
        calendar_entry["alternate1_booking_date"] = request.a1_date
        calendar_entry["alternate1_start_time"] = request.a1_time
        calendar_entry["alternate2_booking_date"] = request.a2_date
        calendar_entry["alternate2_start_time"] = request.a2_time
        calendar_entry["timestamp"] = request.timestamp
        calendar_entry["booking_status"] = request.status
        calendar_entry["id"] = request.messageid
        return calendar_entry

def run_client(_connection_port):
    global writeLog
    with grpc.insecure_channel('localhost:{}'.format(_connection_port)) as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        for response in stub.anti_entropy(yield_entries()):
            #print(response)
            recordFound = False
            for i in range(0,len(writeLog)):
                eachBooking = writeLog[i]
                if eachBooking["id"] == response.messageid:
                    recordFound = True
                    if primary != 1:
                        calendar_entry = make_new_object(response)
                        #eachBooking['booking_status'] = response.status
                        writeLog[i] = calendar_entry
                    break
            if recordFound == False:
                calendar_entry =  make_new_object(response)
                writeLog.append(calendar_entry)
        print(writeLog)
        print('$$$$$$$$$$$$$$$$$$$$$$$$$')
	
	

class BayouServer(a_e_pb2_grpc.BayouServicer):
    def __init__(self):
        global writeLog
        global _connection_ports
        global iteration
        threading.Thread(target=self.execute_anti_entropy, daemon=True).start()
        
    def execute_anti_entropy(self):
        global primary
        '''for i in range(0, r.llen(redisList)):
            eachBooking = literal_eval(r.lindex(redisList, i).decode('utf-8'))
            writeLog.append(eachBooking)'''
        while True:
            print('goin to sleep')
            time.sleep(5)
            try:
                for connection_port in _connection_ports:
                    run_client(str(connection_port))
            except:
                print("no other server")
                if primary == 1:
                    self.executeRequests()

    def anti_entropy(self,request_iterator,context):
        #self.new_list = []
        global writeLog
        for request in request_iterator:
            print("Request: ", request)

            calendar_entry = {}

            calendar_entry["username"] = request.username
            calendar_entry["room_no"] = request.room_no
            calendar_entry["booking_date"] = request.b_date
            calendar_entry["start_time"] = request.b_time
            calendar_entry["alternate1_booking_date"] = request.a1_date
            calendar_entry["alternate1_start_time"] = request.a1_time
            calendar_entry["alternate2_booking_date"] = request.a2_date
            calendar_entry["alternate2_start_time"] = request.a2_time
            calendar_entry["timestamp"] = request.timestamp
            calendar_entry["booking_status"] = request.status
            calendar_entry["id"] = request.messageid

            bookingStat = checkbookingAE(calendar_entry)
            if bookingStat == 'AlreadyInList':
                continue
            elif bookingStat == 'CanBeDone': #called for first preferred timestamp
                #self.new_list.append(calendar_entry)
                writeLog.append(calendar_entry)
            else: # check for alternate booking prefernce
                if calendar_entry["alternate1_booking_date"]!= "" and calendar_entry["alternate1_start_time"]!="":
                    calendar_entry["booking_date"] = calendar_entry["alternate1_booking_date"]
                    calendar_entry["start_time"] = calendar_entry["alternate1_start_time"]
                    calendar_entry["alternate1_booking_date"]= ""
                    calendar_entry["alternate1_start_time"] = ""
                    alternateBookingStat = checkbookingAE(calendar_entry) #called for first preferred timestamp
                    if bookingStat == 'AlreadyInList':
                        continue
                    elif alternateBookingStat == 'CanBeDone':
                        #self.new_list.append(calendar_entry)
                        writeLog.append(calendar_entry)
                    else:
                        if calendar_entry["alternate2_booking_date"]!= "" and calendar_entry["alternate2_start_time"]!="":
                            calendar_entry["booking_date"] = calendar_entry["alternate2_booking_date"]
                            calendar_entry["start_time"] = calendar_entry["alternate2_start_time"]
                            calendar_entry["alternate2_booking_date"]= ""
                            calendar_entry["alternate2_start_time"] = ""
                            alternate2BookingStat = checkbookingAE(calendar_entry) #called for first preferred timestamp
                            if bookingStat == 'AlreadyInList':
                                continue
                            elif alternate2BookingStat == 'CanBeDone':
                                #self.new_list.append(calendar_entry)
                                writeLog.append(calendar_entry)
                            else:
                                calendar_entry["booking_status"] = 'shouldBeDeleted'
                                #self.new_list.append(calendar_entry)
                                writeLog.append(calendar_entry)
                elif calendar_entry["alternate2_booking_date"]!= "" and calendar_entry["alternate2_start_time"]!="":
                    calendar_entry["booking_date"] = calendar_entry["alternate2_booking_date"]
                    calendar_entry["start_time"] = calendar_entry["alternate2_start_time"]
                    calendar_entry["alternate2_booking_date"]= ""
                    calendar_entry["alternate2_start_time"] = ""
                    alternate2BookingStat = checkbookingAE(calendar_entry) #called for first preferred timestamp
                    if bookingStat == 'AlreadyInList':
                        continue
                    if alternate2BookingStat == 'CanBeDone':
                        #self.new_list.append(calendar_entry)
                        writeLog.append(calendar_entry)
                    else:
                        calendar_entry["booking_status"] = 'shouldBeDeleted'
                        #self.new_list.append(calendar_entry)
                        writeLog.append(calendar_entry)
                else:
                    calendar_entry["booking_status"] = 'shouldBeDeleted'
                    #self.new_list.append(calendar_entry)
                    writeLog.append(calendar_entry)

        if primary == 1: #If it's a primary server then it has to take a final decision
            self.sortWriteLogs()
        for item in writeLog:
            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                            username = item["username"],
                                            room_no = item["room_no"],
                                            b_date = item["booking_date"],
                                            b_time = item["start_time"],
                                            a1_date = item["alternate1_booking_date"],
                                            a1_time = item["alternate1_start_time"],
                                            a2_date = item["alternate2_booking_date"],
                                            a2_time = item["alternate2_start_time"],
                                            timestamp = item["timestamp"],
                                            status = item["booking_status"])
    def sortWriteLogs(self):
        global writeLog
        writeLog.sort(key=lambda x:x['timestamp'])
        self.executeRequests()
    
    def executeRequests(self):
        global writeLog
        global iteration
        iteration += 1
        for i in range(0,len(writeLog)):
        #for booking in writeLog:
            booking = writeLog[i]
            if booking['booking_status'] == 'tentative' or booking['booking_status'] == 'shouldBeDeleted':
                #returnStat = self.executeInDB(booking)
                #if returnStat == 'committed':
                if booking['booking_status'] == 'tentative' and iteration == 4:
                    booking['booking_status'] = 'committed'
                    writeLog[i] = booking
                #elif returnStat == 'deleted':
                elif booking['booking_status'] == 'shouldBeDeleted':
                    print('Deleted: ',booking)
                    booking['booking_status'] = 'deleted'
                    writeLog[i] = booking
                else:
                    print('Tentative: ',booking)
        if iteration == 4:
            iteration = 0
    
    '''def executeInDB(self, bookingRequest):
        if bookingRequest['booking_status'] == 'shouldBeDeleted':
            bookingRequest['booking_status'] = 'deleted'
            r.lpush(redisList,bookingRequest)
            return 'deleted'
        elif iteration == 4:
            bookingRequest['booking_status'] = 'committed'
            r.lpush(redisList,bookingRequest)
            return 'committed'
        return '''''


def run_server(_server_port,_connection_ports,_rest_server):
    print('Ports: {}, {}, {}'.format(_server_port,_connection_ports,_rest_server))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:{}'.format(_server_port))
    server.start()

    try:
        threading.Thread(target=app.run(port=_rest_server,debug=True), daemon=True).start()
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

    for i in range(0,len(writeLog)):
        eachBooking = writeLog[i]
        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if(eachBooking["start_time"]==booking_info["start_time"]):
                bookingAvail=False
                return bookingAvail
    return bookingAvail

def bookRoom(booking_info):
    global writeLog
    if(checkBooking(booking_info)):
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
        booking_info["id"]=str(id) + str(sys.argv[1])
        booking_info["timestamp"]=str(time.time())
        booking_info["booking_status"]="tentative"
        print(booking_info)
        if(bookRoom(booking_info)): return 'Tentatively booked primary or alternate slot.',201
        else: return 'Booking slots unavailable.', 304

class GetBooking(Resource):

	def get(self, username):
		users_bookings = dict()
		user_booking_list_item = []
		global writeLog
		for i in range(0, len(writeLog)):
			users_bookings_item = {}
			eachBooking = writeLog[i]
			print("Got record {} from writeLog".format(eachBooking))
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

