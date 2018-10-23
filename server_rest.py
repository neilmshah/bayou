from flask import Flask, request, jsonify, json, Response
from flask_restful import Resource, Api, reqparse, abort
import redis
import time
from ast import literal_eval

app = Flask(__name__)
api = Api(app)

r = redis.StrictRedis(host='localhost', port=6000, db=0)

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
	#   "timestamp" : 00000.00000
	#   "booking_status": "Tentative/Committed"
	#   "id": id
	# }
# }


parser = reqparse.RequestParser()
parser.add_argument("booking_info")


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
		r.lpush("bookings",booking_info)
		return True
	else:
		if(booking_info["alternate1_booking_date"]!="" and booking_info["alternate1_booking_date"]!=""):
			booking_info["booking_date"]=booking_info["alternate1_booking_date"]
			booking_info["start_time"]=booking_info["alternate1_start_time"]
			booking_info["alternate1_booking_date"]=""
			booking_info["alternate1_start_time"]=""
			if(checkBooking(booking_info)):
				print("Pushing alt1 to redis")
				r.lpush("bookings",booking_info)
				print("successfully alt1 pushed to redis")
				return True
			else:
				if(booking_info["alternate2_booking_date"]!="" and booking_info["alternate2_booking_date"]!=""):
					booking_info["booking_date"]=booking_info["alternate2_booking_date"]
					booking_info["start_time"]=booking_info["alternate2_start_time"]
					booking_info["alternate2_booking_date"]=""
					booking_info["alternate2_start_time"]=""
					if(checkBooking(booking_info)):
						r.lpush("bookings",booking_info)
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
		for i in range(0, r.llen("bookings")):
			users_bookings_item = {}
			eachBooking = literal_eval(r.lindex("bookings", i).decode('utf-8'))
			if eachBooking["user_name"] == username:
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
	app.run(port='3000', debug=True)
