from concurrent import futures
import time

import grpc

import a_e_pb2
import a_e_pb2_grpc

import sys
import time
import yaml

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

_server_port = 3000
_connection_port = 4000

l = [1,2,3,4,5]

booking_list = []

def init_dummy(dummy_data):

    calendar_entry = {}

    one = dummy_data['one']
    two = dummy_data['two']

    calendar_entry["username"] = "sha"
    calendar_entry["room_no"] = str(one[0])
    calendar_entry["booking_date"] = str(one[1])
    calendar_entry["start_time"] = str(one[2])
    calendar_entry["alternate1_booking_date"] = str(one[3])
    calendar_entry["alternate1_start_time"] = str(one[4])
    calendar_entry["timestamp"] = str(one[5])
    calendar_entry["booking_status"] = str("tentative")
    calendar_entry["id"] = str(one[6])
    #print(calendar_entry)
    booking_list.append(calendar_entry)

    print("Initial Entries")
    print(calendar_entry["room_no"]+" "+calendar_entry["room_no"]+" "+calendar_entry["start_time"])


    calendar_entry = {}

    calendar_entry["username"] = "sha"
    calendar_entry["room_no"] = str(two[0])
    calendar_entry["booking_date"] = str(two[1])
    calendar_entry["start_time"] = str(two[2])
    calendar_entry["alternate1_booking_date"] = ""
    calendar_entry["alternate1_start_time"] = ""
    calendar_entry["timestamp"] = str(two[3])
    calendar_entry["booking_status"] = "tentative"
    calendar_entry["id"] = str(two[4])

    #print(calendar_entry)
    booking_list.append(calendar_entry)



def yield_entries():
    for i in l:
        yield a_e_pb2.test(num = i)

def yield_entry():

    for item in booking_list:
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

def run_client(_connection_port):

    with grpc.insecure_channel('localhost:'+_connection_port) as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        responses = stub.anti_entropy(yield_entry())

        for response in responses:
            #print(response.num)
            pass

def does_entry_exists(id):
    for item in booking_list:
        if item['id'] == id:
            return True
    
    return False

def checkbooking(booking_info):
    global booking_list
    bookingAvail = True
    for i in range(0,len(booking_list)):
        eachBooking = booking_list[i]

        if(eachBooking["id"] == booking_info["id"]):
            print("id match")
            bookingAvail = False
            break


        if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
            if((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] < booking_info["timestamp"]) ): 
                print("start time of server list less")
                bookingAvail=False
                break
            if ((eachBooking["start_time"] == booking_info["start_time"]) and (eachBooking["timestamp"] > booking_info["timestamp"]) ):
                eachBooking['start_date'] = eachBooking["alternate1_booking_date"]
                eachBooking['start_time'] = eachBooking["alternate1_start_time"]
                eachBooking["alternate1_booking_date"] = ""
                eachBooking["alternate1_start_time"] = ""
                booking_list.append(eachBooking)

                del booking_list[i]

    return bookingAvail

class BayouServer(a_e_pb2_grpc.BayouServicer):
    
    def __init__(self):
        self.new_list = []

    def make_new_object(self,request):
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

        return calendar_entry


    def anti_entropy(self,request_iterator,context):
        self.new_list = []
        global booking_list

        for request in request_iterator:
            #print(request.messageid)

            calendar_entry = self.make_new_object(request)

            #print(calendar_entry)
            """
            flag = True
            for item in booking_list:

                if item['id'] == calendar_entry['id']:
                    #print("this is called-1")
                    flag = False
                    break

                if item['room_no'] == calendar_entry['room_no'] and item['start_time'] == calendar_entry['start_time']:
                    if item['timestamp'] <= calendar_entry['timestamp']:
                        #print('this is called-2')
                        flag = False
                        break
                    else:
                        #update the new values to the existing one
                        pass
            """
            if checkbooking(calendar_entry):
                #print('this is called-3') 
                self.new_list.append(calendar_entry)

        booking_list += self.new_list

        #print(len(booking_list))
        for item in booking_list:
            print(item["id"]+" "+item["booking_date"]+" "+item["start_time"])

        print("$$")

        for item in booking_list:

            yield a_e_pb2.calendarEntry(messageid = item["id"],
                                        username = item["username"],
                                        room_no = item["room_no"],
                                        b_date = item["booking_date"],
                                        b_time = item["start_time"],
                                        a1_date = item["alternate1_booking_date"],
                                        a1_time = item["alternate1_start_time"],
                                        timestamp = item["timestamp"],
                                        status = item["booking_status"])

    def checktest(self,request_iterator,context):
        for request in request_iterator:
            print(request.num)
            self.new_list.append(request.num)

        for item in self.new_list:
            yield a_e_pb2.test(num = item)


def run_server(_server_port,_connection_ports):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:'+_server_port)

    server.start()

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

if __name__ == '__main__':

    config_dict = yaml.load(open('config.yaml'))

    config_dict = config_dict[str(sys.argv[1])]

    _server_port = str(config_dict['server_port'])
    _connection_ports = config_dict['connection_port']

    dummy_data = config_dict['dummy_data']
    init_dummy(dummy_data)

    run_server(_server_port,_connection_ports)

