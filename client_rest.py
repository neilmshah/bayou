import sys
import requests
import json

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
	serverhost = "localhost"
	serverport = 5000

	def __init__(self):
			self.meetingRoomData["booking_info"] = {}
			self.meetingRoomData["booking_info"]["username"] = sys.argv[1]

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


	def print_meeting_details(self):
		print(self.meetingRoomData)


	def send_meeting_details(self):
		url = "{}{}{}{}{}".format("http://",self.serverhost, ":", self.serverport, "/booking")
		print ("url being invoked is : {}" .format(url))
		requests.post(url, data =json.dumps(self.meetingRoomData))


if __name__ == '__main__':
	print("Welcome to Spartan Room Booking system.")
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

	c.print_meeting_details()

	c.send_meeting_details()
