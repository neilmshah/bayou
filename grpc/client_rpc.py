"""
NO NEED TO USE THIS
"""
from concurrent import futures
import grpc
import a_e_pb2
import a_e_pb2_grpc




l = [1,2,3,4,5]

def send_numbers():
    for i in l:
        yield a_e_pb2.test(num = i)

def run_client():
    with grpc.insecure_channel('localhost:3000') as channel:
        stub = a_e_pb2_grpc.BayouStub(channel)

        responses = stub.checktest(send_numbers())

        for response in responses:
            print(response.num)

if __name__ == '__main__':
    run_client()