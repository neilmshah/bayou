import sys
import requests
import json
import yaml
import time
from termcolor import colored



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


class Client:

	meetingRoomData = dict()
	serverhost = ""
	serverport = ""
	username = ""

	def __init__(self):

		self.meetingRoomData = {}
		self.username = sys.argv[1]
		self.meetingRoomData["username"] = self.username
		with open("config.yaml", 'r') as stream:
			try:
				configs = yaml.load(stream)
				group1clients = configs['rest_server1_clients']
				for i in range(0, len(group1clients)):
					if self.meetingRoomData["username"] == group1clients[i]:
						server_details = configs['one']
						self.serverhost = server_details['hostname']
						self.serverport = server_details['rest_server_port']
						break

				if self.serverhost == "":
					group2clients = configs['rest_server2_clients']
					for i in range(0, len(group2clients)):
						if self.meetingRoomData["username"] == group2clients[i]:
							server_details = configs['two']
							self.serverhost = server_details['hostname']
							self.serverport = server_details['rest_server_port']
							break

				# default server or all other users
				if self.serverhost == "":
					server_details = configs['three']
					self.serverhost = server_details['hostname']
					self.serverport = server_details['rest_server_port']

				stream.close()

			except yaml.YAMLError as exc:
				print(exc)



	def get_meeting_details(self,iteration,alernatives):
		valid_user_data = False
		if iteration == 1:
			room_no = str(input("Room no : "))

			if room_no != "":
				self.meetingRoomData["room_no"] = room_no

			booking_date = str(input("Date (mm/dd/yy) : "))

			if booking_date != "":
				self.meetingRoomData["booking_date"] = booking_date

			start_time = str(input("Start Time : "))

			if start_time != "":
				self.meetingRoomData["start_time"] = start_time

			if room_no != "" and booking_date != "" and start_time != "":
				valid_user_data = True

		elif iteration == 2:
			if alternatives.upper() == "Y":

				alernative_date1 = str(input("Date (mm/dd/yy) : "))

				if alernative_date1 != "":
					self.meetingRoomData["alternate1_booking_date"] = alernative_date1

				alernative_start_time = str(input("Start Time : "))

				if alernative_start_time != "":
					self.meetingRoomData["alternate1_start_time"] = alernative_start_time
			else:
				self.meetingRoomData["alternate1_booking_date"] = ""
				self.meetingRoomData["alternate1_start_time"] = ""

		elif iteration == 3:
			if alternatives.upper() == "Y":
				alternate2_booking_date = str(input("Date (mm/dd/yy) : "))
				if alternate2_booking_date != "":
					self.meetingRoomData["alternate2_booking_date"] = alternate2_booking_date

				alternate2_start_time = str(input("Start Time : "))
				if alternate2_start_time != "":
					self.meetingRoomData["alternate2_start_time"] = alternate2_start_time
			else:
				self.meetingRoomData["alternate2_booking_date"] = ""
				self.meetingRoomData["alternate2_start_time"] = ""

		return valid_user_data

	def send_meeting_details(self):
		url = "{}{}{}{}{}".format("http://",self.serverhost, ":", self.serverport, "/booking")

		try:
			response = requests.post(url, data={"booking_info": json.dumps(self.meetingRoomData)})
		except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError):
			print("Error connecting to server. Please retry again later.")

		if response.status_code == 201:
			print("\nSuccessfully submitted a booking request for room: {}".format(self.meetingRoomData["room_no"]))
		else:
			print("\nSorry! This room has already been taken. Please try a different room/time")

	def get_reservation_status(self):
		url = "{}{}{}{}{}{}".format("http://",self.serverhost, ":", self.serverport, "/booking/",self.username,)
		print("Room\tDate\tStarts\tEnds\tStatus")
		while True:
			r = requests.get(url)
			response = json.loads(r.content)
			bookings_list = response[self.username]

			if len(bookings_list) > 0:
				committed_count = 0
			else:
				print("No bookings available for {}" .format(self.username))

			for l in range(0,len(bookings_list)):
				booking_list_item = bookings_list[l]
				end_time = int(booking_list_item["start_time"])+1
				if booking_list_item["booking_status"].upper() == "TENTATIVE":

					print(colored('{}\t{}\t{}\t{}\t{}','yellow').format(booking_list_item["room_no"], booking_list_item["booking_date"], booking_list_item["start_time"], end_time, booking_list_item["booking_status"]))
				elif booking_list_item["booking_status"].upper() == "COMMITTED":
					print(colored('{}\t{}\t{}\t{}\t{}','green').format(booking_list_item["room_no"],booking_list_item["booking_date"], booking_list_item["start_time"], end_time, booking_list_item["booking_status"]))
				else:
					print(colored('{}\t{}\t{}\t{}\t{}', 'red').format(booking_list_item["room_no"],
				        booking_list_item["booking_date"],booking_list_item["start_time"], end_time,booking_list_item["booking_status"]))

				time.sleep(1)

				if booking_list_item["booking_status"].upper() == "COMMITTED" or booking_list_item["booking_status"].upper() == "DELETED":
					committed_count +=1

			if len(bookings_list) == 0 or len(bookings_list) == committed_count:
				break

			time.sleep(5)

if __name__ == '__main__':

	print("Welcome to Spartan library room booking system.")
	if len(sys.argv) < 2 or len(sys.argv) > 2:
		print("Usage: python3 client.py <<username>>")
		exit()

	c = Client()
	n = 1
	alternatives = "n"

	if c.get_meeting_details(n, alternatives):

		alternatives = str(input("\nDo you want to provide alternative booking times? (y/n):"))

		while n < 3:
			n += 1
			c.get_meeting_details(n, alternatives)

			if n < 3 and alternatives.upper() == "Y":
				alternatives = str(input("\nDo you want to provide alternative booking times? (y/n):"))

		c.send_meeting_details()

	else:
		print ("\nSorry, correct data was not entered. Please retry again.")


	choice = str(input("\nCheck your previous booking status? (y/n):"))

	if choice.upper() == "Y":
		c.get_reservation_status()
