from flask import Flask, request, jsonify, json, Response
from flask_restful import Resource, Api, reqparse, abort
import redis
import time
from ast import literal_eval
import yaml
import sys

app = Flask(__name__)
api = Api(app)

r = redis.StrictRedis(host='localhost', port=6379, db=0)

id = 0
#_server_port = 3000
#_connection_port = 4000
#redisList = "bookings"

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
	#   "timestamp" : 00000.00000
	#   "booking_status": "Tentative/Committed"
	#   "id": id
	# }
# }


parser = reqparse.RequestParser()
parser.add_argument("booking_info")


def checkBooking(booking_info):
	bookingAvail = True

	for i in range(0, r.llen(redisList)):
		eachBooking = literal_eval(r.lindex(redisList, i).decode('utf-8'))
		if(eachBooking["room_no"]==booking_info["room_no"] and eachBooking["booking_date"]==booking_info["booking_date"]):
			if(eachBooking["start_time"]==booking_info["start_time"]):
				bookingAvail=False
				break
	return bookingAvail

def bookRoom(booking_info):
	if(checkBooking(booking_info)):
		r.lpush(redisList,booking_info)
		return True
	else:
		if(booking_info["alternate1_booking_date"]!="" and booking_info["alternate1_booking_date"]!=""):
			booking_info["booking_date"]=booking_info["alternate1_booking_date"]
			booking_info["start_time"]=booking_info["alternate1_start_time"]
			booking_info["alternate1_booking_date"]=""
			booking_info["alternate1_start_time"]=""
			if(checkBooking(booking_info)):
				r.lpush(redisList,booking_info)
				return True
			else:
				if(booking_info["alternate2_booking_date"]!="" and booking_info["alternate2_booking_date"]!=""):
					booking_info["booking_date"]=booking_info["alternate2_booking_date"]
					booking_info["start_time"]=booking_info["alternate2_start_time"]
					booking_info["alternate2_booking_date"]=""
					booking_info["alternate2_start_time"]=""
					if(checkBooking(booking_info)):
						r.lpush(redisList,booking_info)
						return True
	return False

class BookRoom(Resource):
	def post(self):
		args = parser.parse_args()
		booking_info = literal_eval(args["booking_info"])
		global id
		id += 1
		booking_info["id"]=id
		booking_info["timestamp"]=time.time()
		booking_info["booking_status"]="tentative"
		print(booking_info)
		if(bookRoom(booking_info)): return 'Tentatively booked primary or alternate slot.',201
		else: return 'Booking slots unavailable.', 304
		#return '', 201

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

if __name__ == '__main__':

	global _server_port
	global _connection_port
	global redisList
	config_dict = yaml.load(open('config.yaml'))
	config_dict = config_dict[str(sys.argv[1])]
	_server_port = str(config_dict['server_port'])
	_connection_ports = config_dict['connection_port']
	redisList = "bookings" + str(_server_port)

    #dummy_data = config_dict['dummy_data']
    #init_dummy(dummy_data)

    #run_server(_server_port,_connection_ports)
	print("Starting server on port " + str(_server_port))
	app.run(port=_server_port, debug=True)
