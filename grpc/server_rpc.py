from concurrent import futures
import time

import grpc

import a_e_pb2
import a_e_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

_server_port = 3000
_connection_port = 4000

l = [1,2,3,4,5]

def yield_entries():
    for i in l:
        yield a_e_pb2.test(num = i)

def run_client():
    with grpc.insecure_channel('localhost:3000') as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        responses = stub.checktest(yield_entries())

        for response in responses:
            print(response.num)

class BayouServer(a_e_pb2_grpc.BayouServicer):
    
    def __init__(self):
        self.new_list = []

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

    def checktest(self,request_iterator,context):
        for request in request_iterator:
            print(request.num)
            self.new_list.append(request.num)

        for item in self.new_list:
            yield a_e_pb2.test(num = item)


def run_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    a_e_pb2_grpc.add_BayouServicer_to_server(BayouServer(),server)
    server.add_insecure_port('[::]:4000')

    server.start()

    try:
        run_client()
    except:
        print("no other server")

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    run_server()

