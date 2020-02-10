import socket
import time
import pickle
import random


class IPingEmulator:

	SERVER_PORT = 1234
	BUFFER_SIZE = 1024
	REQUEST_MAGIC_NUMBER = 246246
	REPLY_MAGIC_NUMBER = 135135

	class PingPacket:

		def __init__(self, generated_random_number, magic_number):
			self.magic_number = magic_number
			self.generated_random_number = generated_random_number
		
