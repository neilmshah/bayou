import sys
import requests
import json
import yaml


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

	def __init__(self):

		self.meetingRoomData["booking_info"] = {}

		self.meetingRoomData["booking_info"]["username"] = sys.argv[1]

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

		requests.post(url, data=json.dumps(self.meetingRoomData))


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
			n += 1
			c.get_meeting_details(n)
		else:
			break

	c.send_meeting_details()
