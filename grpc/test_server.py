from concurrent import futures
import time

import grpc
import redis
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse, abort
from ast import literal_eval
import a_e_pb2
import a_e_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

_server_port = 4000
_connection_port = 3000
_rest_server = 7000
_redis_port = 6379

n = [{"timestamp": "1122", "val": 1}, {"timestamp": "0012", "val": 2}]
m = [{"timestamp": "1234", "val": 4}, {"timestamp": "3456", "val": 3}]
l = [1,2,3]
writeLog = []
r = redis.StrictRedis(host='localhost', port=_redis_port, db=0)

def yield_entries():
    '''for i in l:
        yield a_e_pb2.test(num = i)'''
    for i in writeLog:
        yield a_e_pb2.calendarEntry(writeLog.pop(i))

def run_client():
    with grpc.insecure_channel('localhost:{}'.format(_connection_port)) as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        responses = stub.anti_entropy(yield_entries())
        #responses = stub.checktest(yield_entries())
        print(responses)
        for response in responses:
            print(response)

class BayouServer(a_e_pb2_grpc.BayouServicer):
    def __init__(self):
        self.new_list = []
        self.writeLog = []

    def anti_entropy(self,request_iterator,context):
        for request in request_iterator:

            calendar_entry = {}

            calendar_entry["username"] = request.username
            calendar_entry["room_no"] = request.room_no
            calendar_entry["booking_date"] = request.b_date
            calendar_entry["start_time"] = request.b_time
            calendar_entry["timestamp"] = request.timestamp
            calendar_entry["booking_status"] = request.status
            calendar_entry["id"] = request.messageid

            self.new_list.append(calendar_entry)

        for item in self.new_list:

            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                        username = item["username"],
                                        room_no = item["room_no"],
                                        b_date = item["booking_date"],
                                        b_time = item["start_time"],
                                        timestamp = item["timestamp"],
                                        status = item["booking_status"])
        self.mergeWriteLogs()

    def checktest(self,request_iterator,context):
        global m
        global n
        self.new_list = []
        
        for request in request_iterator:
            print(request.num)
            self.new_list.append(request.num)
        m += n
        m.sort(key=lambda x:x['timestamp'])
        for item in m:
            print("item = ",item)
        #self.new_list.sort(key=lambda x:x['timestamp'])
        for item in self.new_list:
            yield a_e_pb2.test(num = item)

    def mergeWriteLogs(self):
        self.writeLog += self.new_list
        self.writeLog.sort(key=lambda x:x['timestamp'])
        self.executeRequests()
    
    def executeRequests(self):
        for booking in self.writeLog:
            bookRoom(booking)


def run_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:{}'.format(_server_port))
    server.start()
    #app.run(port=_rest_server, debug=True)

    try:
        run_client()
    except:
        print("no other server")

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

# --------Rest-----------
app = Flask(__name__)
api = Api(app)

id = 0
bookings = "bookings"

#meetingRoom data-structure:
# { "booking_info": {
    #   "username": "abc"
    #   "room_no" : "123"
    #   "booking_date" : "mm-dd-yyyy"
    #   "start_time": "9"
    #   "alternate1_booking_date" : "mm-dd-yyyy"
    #   "alternate1_start_time": "9"
    #   "alternate2_booking_date" : "mm-dd-yyyy"
    #   "alternate2_start_time": "9"
    #   "timestamp" : "00:00:00"
    #   "booking_status": "Tentative/Committed"
    #   "id": id
    # }
# }


parser = reqparse.RequestParser()
parser.add_argument('booking_info', type=dict)

def checkBooking(booking_info):
    bookingAvail = True

    for i in range(0, r.llen("bookings")):
        eachBooking = literal_eval(r.lindex("bookings", i).decode('utf-8'))
        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if(eachBooking["start_time"]==booking_info["start_time"]): 
                bookingAvail=False
                break
    return bookingAvail

def bookRoom(booking_info):
    if(checkBooking(booking_info)): 
        r.lpush(booking_info)
        return True
    else:
        if(booking_info["alternate1_booking_date"]!="" and booking_info["alternate1_booking_date"]!=""):
            booking_info["booking_date"]=booking_info["alternate1_booking_date"]
            booking_info["start_time"]=booking_info["alternate1_start_time"]
            booking_info["alternate1_booking_date"]=""
            booking_info["alternate1_start_time"]=""
            if(checkBooking(booking_info)): 
                r.lpush(booking_info)
                return True
        else:
            if(booking_info["alternate2_booking_date"]!="" and booking_info["alternate2_booking_date"]!=""):
                booking_info["booking_date"]=booking_info["alternate2_booking_date"]
                booking_info["start_time"]=booking_info["alternate2_start_time"]
                booking_info["alternate2_booking_date"]=""
                booking_info["alternate2_start_time"]=""
                if(checkBooking(booking_info)): 
                    r.lpush(booking_info)
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

if __name__ == '__main__':
    run_server()

