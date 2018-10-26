from concurrent import futures
import time

import grpc
import redis
from flask import Flask, request, jsonify
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
#_server_port = 3000
#_connection_ports = 4000
#_rest_server = 5000
_redis_port = 6379
redisList = ""
dummy_booking_date = {
    "username": "abc",
    "room_no" : "123",
    "booking_date" : "mm-dd-yyyy",
    "start_time": "15",
    "alternate1_booking_date" : "mm-dd-yyyy",
    "alternate1_start_time": "9",
    "alternate2_booking_date" : "mm-dd-yyyy",
    "alternate2_start_time": "9",
    "booking_status": "Tentative",
    "id": "0",
    "timestamp": "10"
    }
writeLog.append(dummy_booking_date)
r = redis.StrictRedis(host='localhost', port=_redis_port, db=0)

def yield_entries():
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
    bookingAvail = True
    for i in range(0,len(writeLog)):
        eachBooking = writeLog[i]

        if(eachBooking["id"] == booking_info["id"]):
            #print("id match")
            bookingAvail = False
            break


        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] <= booking_info["timestamp"]) ): 
                print("start time of server list less")
                bookingAvail=False
                break
            if ((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] > booking_info["timestamp"]) ):
                eachBooking['start_date'] = eachBooking["alternate1_booking_date"]
                eachBooking['start_time'] = eachBooking["alternate1_start_time"]
                eachBooking["alternate1_booking_date"] = ""
                eachBooking["alternate1_start_time"] = ""
                writeLog.append(eachBooking)

                del writeLog[i]

    return bookingAvail

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

        if checkbookingAE(calendar_entry):
                print("i was called lol")
                self.new_list.append(calendar_entry)

    
        writeLog += self.new_list

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
    def mergeWriteLogs(self):
        global writeLog
        writeLog += self.new_list
        writeLog.sort(key=lambda x:x['timestamp'])
        self.executeRequests()
    
    def executeRequests(self):
        for booking in writeLog:
            if bookRoom(booking):
                print('Commited: ',booking)
                writeLog.index([booking])['booking_status'] = 'Commited'
            else:
                writeLog.remove(booking)

def run_server(_server_port,_connection_ports,_rest_server):
    print('Ports: {}, {}, {}'.format(_server_port,_connection_ports,_rest_server))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:{}'.format(_server_port))
    server.start()
    '''try:
        t = threading.Thread(target=app.run(), args=(_rest_server,True))
        t.start()
    except:
        print('Rest server connection error: ',_rest_server)'''


    

    while True:
        #anti-entropy time
        time.sleep(5)

        #print(_server_port)

        try:
            for connection_port in _connection_ports:
                run_client(str(connection_port))
        except:
            print("no other server")

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
	



# --------Rest-------------------
app = Flask(__name__)
api = Api(app)

id = 0
bookings = "bookings"


parser = reqparse.RequestParser()
parser.add_argument(redisList, type=dict)

def checkBooking(booking_info):
    bookingAvail = True

    for i in range(0, 1):
        eachBooking = eval(r.hget(redisList, i+1))
        print(eachBooking)
        #eachBooking = literal_eval(r.lindex("bookings", i).decode('utf-8'))
        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if(eachBooking["start_time"]==booking_info["start_time"]): 
                bookingAvail=False
                break
    return bookingAvail

def bookRoom(booking_info):
    if(checkBooking(booking_info)): 
        #r.lpush(booking_info)
        r.hset(redisList, booking_info['id'], booking_info)
        return True
    else:
        if(booking_info["alternate1_booking_date"]!="" and booking_info["alternate1_booking_date"]!=""):
            booking_info["booking_date"]=booking_info["alternate1_booking_date"]
            booking_info["start_time"]=booking_info["alternate1_start_time"]
            booking_info["alternate1_booking_date"]=""
            booking_info["alternate1_start_time"]=""
            if(checkBooking(booking_info)): 
                #r.lpush(booking_info)
                r.hset('booking_info', booking_info['id'], booking_info)
                return True
        else:
            if(booking_info["alternate2_booking_date"]!="" and booking_info["alternate2_booking_date"]!=""):
                booking_info["booking_date"]=booking_info["alternate2_booking_date"]
                booking_info["start_time"]=booking_info["alternate2_start_time"]
                booking_info["alternate2_booking_date"]=""
                booking_info["alternate2_start_time"]=""
                if(checkBooking(booking_info)): 
                    #r.lpush(booking_info)
                    r.hset('booking_info', booking_info['id'], booking_info)
                    return True
    return False

class BookRoom(Resource):
    def post(self):
        args = parser.parse_args()
        booking_info = args["booking_info"]
        global id
        id += 1
        booking_info["id"]=id
        booking_info["timestamp"]=time.time()
        booking_info["booking_status"]="tentative"
        if(bookRoom(booking_info)): return 'Tentatively booked primary or alternate slot.',201
        else: return 'Booking slots unavailable.', 304

class GetBooking(Resource):
    def get(self, username):
        #TO-DO

        return '',404

api.add_resource(GetBooking, '/booking/<string:username>')
api.add_resource(BookRoom, '/booking')


# ----------------------Main--------------------
if __name__ == '__main__':

    config_dict = yaml.load(open('config.yaml'))

    config_dict = config_dict[str(sys.argv[1])]

    _server_port = str(config_dict['server_port'])
    _connection_ports = config_dict['connection_port']
    _rest_server_port = config_dict['rest_server_port']
    redisList = "bookings" + str(_server_port)
    run_server(_server_port,_connection_ports, _rest_server_port)


