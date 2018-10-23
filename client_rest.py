import sys
import requests
import json
import yaml
import time


#meetingRoom data-structure:
# {
#   "username": "abc"
#   "room_no" : "123"
#   "booking_date" : "mm-dd-yyyy"
#   "start_time": "9"
#   "end_time" : "10"
#   "alternate1_booking_date" : "mm-dd-yyyy"
#   "alternate1_start_time": "9"
#   "alternate1_end_time" : "10"
#   "alternate2_booking_date" : "mm-dd-yyyy"
#   "alternate2_start_time": "9"
#   "alternate2_end_time" : "10"
#   "timestamp" : "00:00:00"
#   "booking_status": "Tentative/Committed"
# }


class Client:

	meetingRoomData = dict()
	serverhost = ""
	serverport = ""
	username = ""

	def __init__(self):

		self.meetingRoomData["booking_info"] = {}

		self.username = sys.argv[1]

		self.meetingRoomData["booking_info"]["username"] = self.username

		with open("config.yaml", 'r') as stream:
			try:
				configs = yaml.load(stream)

				group1clients = configs['rest_server1_clients']

				for i in range(0, len(group1clients)):
					if self.meetingRoomData["booking_info"]["username"] == group1clients[i]:
						server_details = configs['rest_server1']
						self.serverhost = server_details['host']
						self.serverport = server_details['port']
						break

				if self.serverhost == "":
					group2clients = configs['rest_server2_clients']

					for i in range(0, len(group2clients)):
						if self.meetingRoomData["booking_info"]["username"] == group2clients[i]:
							server_details = configs['rest_server2']
							self.serverhost = server_details['host']
							self.serverport = server_details['port']
							break

				# default server or all other users
				if self.serverhost == "":
					server_details = configs['default_rest_server']
					self.serverhost = server_details['host']
					self.serverport = server_details['port']

				stream.close()

			except yaml.YAMLError as exc:
				print(exc)




	def get_meeting_details(self,iteration):

		if iteration == 1:
			self.meetingRoomData["booking_info"]["room_no"] = str(input("Room no : "))
			self.meetingRoomData["booking_info"]["booking_date"] = str(input("Date (mm/dd/yy) : "))
			self.meetingRoomData["booking_info"]["start_time"] = str(input("Start Time : "))
		elif iteration == 2:
			self.meetingRoomData["booking_info"]["alternate1_booking_date"] = str(input("Date (mm/dd/yy) : "))
			self.meetingRoomData["booking_info"]["alternate1_start_time"] = str(input("Start Time : "))
		elif iteration == 3:
			self.meetingRoomData["booking_info"]["alternate2_booking_date"] = str(input("Date (mm/dd/yy) : "))
			self.meetingRoomData["booking_info"]["alternate2_start_time"] = str(input("Start Time : "))


	def send_meeting_details(self):
		print("Connecting to Server {}:{} ".format(self.serverhost,self.serverport))
		url = "{}{}{}{}{}".format("http://",self.serverhost, ":", self.serverport, "/booking")
		print ("url being invoked is : {}" .format(url))
		print("meetingRoomData is {}" .format(json.dumps(self.meetingRoomData)))

		requests.post(url, data=json.dumps(self.meetingRoomData))


	def get_reservation_status(self):
		print("Connecting to Server {}:{} ".format(self.serverhost,self.serverport))

		url = "{}{}{}{}{}{}".format("http://",self.serverhost, ":", self.serverport, "/booking/",self.username,)

		while True:

			r = requests.get(url)

			response = json.loads(r.content)

			bookings_list = response[self.username]

			if len(bookings_list) > 0:
				committed_count = 0
				print("Room No, Booking Date, Booking Start Time, Booking Status")
			else:
				print("No Room bookings available for {}" .format(self.username))


			for l in range(0,len(bookings_list)):

				booking_list_item = l[i]

				print ("{},{},{},{}".format(booking_list_item["room_no"], booking_list_item["booking_date"], booking_list_item["booking_start_time"], booking_list_item["booking_status"]))

				if booking_list_item["booking_status"] == "Committed":
					committed_count +=1

			if len(bookings_list) == 0 or len(bookings_list) == committed_count:
				break;

			time.sleep(3)





if __name__ == '__main__':

	print("Welcome to Spartan Room Booking System.")

	if len(sys.argv) < 2 or len(sys.argv) > 2:
		print("Usage: python3 client.py <<username>>")
		exit()

	c = Client()
	n = 1
	c.get_meeting_details(n)

	while n < 3:
		alternatives = str(input("\nDo you want to provide alternative times in case the room is not available at the previously chosen time? (y/n):"))

		if alternatives.upper() == "Y":
			n += 1;
			c.get_meeting_details(n)
		else:
			break

	c.send_meeting_details()

	c.get_reservation_status()
