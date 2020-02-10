import socket
import time
import pickle
import random
import sys

from ping_emulators.i_ping_emulator import IPingEmulator


class ClientPingEmulator(IPingEmulator):
	
	def __init__(self, af, protocol, timeout, address_for_binding="127.0.0.1"):
		self._af = af
		self._timeout = timeout
		self._address_for_binding = address_for_binding
		if protocol == socket.SOCK_DGRAM:
			self.ping = self._emulate_ping_over_UDP
		elif protocol == socket.SOCK_STREAM:
			self.ping = self._emulate_ping_over_TCP
		else:
			raise RuntimeError("invalid protocol")


	def _emulate_ping_over_UDP(self, server_address):
		generated_random_number = random.randint(0, sys.maxsize)
		ping_packet = ClientPingEmulator.PingPacket(generated_random_number, self.REQUEST_MAGIC_NUMBER)
		serialized_msg = pickle.dumps(ping_packet)

		with socket.socket(self._af, socket.SOCK_DGRAM) as sock:
			sock.bind((self._address_for_binding, 0))
			time_sent = time.time()
			bytes_sent = sock.sendto(serialized_msg, (server_address, self.SERVER_PORT))
			if bytes_sent != len(serialized_msg):
				raise RuntimeError("An error occured while sending message over UDP socket:", bytes_sent, "out of", len(serialized_msg), "sent")

			is_ping_replied = self._receive_emulated_ping_reply_over_UDP(sock, generated_random_number, server_address)
			if not is_ping_replied:
				return False

		print("successfully pinged to", server_address, "time elapsed:", time.time() - time_sent)
		return True


	def _receive_emulated_ping_reply_over_UDP(self, sock, generated_random_number, server_address):
		is_ping_replied = False
		start_time = time.time()

		while not is_ping_replied:
			sock.settimeout(self._timeout - (time.time() - start_time))
			try:
				received_data, (msg_src_address, msg_src_port) = sock.recvfrom(self.BUFFER_SIZE)
			except socket.timeout:
				print("Couldn't ping", server_address, "- timeout")
				return False
			if msg_src_address != server_address:
				print("Message source address is", msg_src_address, "when expected address is", server_address)
				continue
			if msg_src_port != self.SERVER_PORT:
				print("Message source port is", msg_src_port, "when expected port is", self.SERVER_PORT)
				continue
			ping_packet = pickle.loads(received_data)
			if ping_packet.magic_number != self.REPLY_MAGIC_NUMBER:
				print("Message magic number is", ping_packet.magic_number, "and not as expected")
				continue
			if ping_packet.generated_random_number != generated_random_number:
				print("Ping reply doesn't match ping request")
				continue
			is_ping_replied = True

		return True


	def _emulate_ping_over_TCP(self, server_address):
		with socket.socket(self._af, socket.SOCK_STREAM) as sock:
			sock.settimeout(self._timeout)
			time_of_connection_try = time.time()
			try:
				sock.connect((server_address, self.SERVER_PORT))
			except socket.timeout:
				print("Couldn't ping", server_address, "- timeout")
				return False
			except ConnectionRefusedError:
				print("Couldn't ping", server_address, "- connection refused")
				return False

		print("successfully pinged to", server_address, "time elapsed:", time.time() - time_of_connection_try)
		return True

