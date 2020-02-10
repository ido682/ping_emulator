import socket
import pickle
import threading

from ping_emulators.i_ping_emulator import IPingEmulator


class ServerPingEmulator(IPingEmulator):
	
	PENDING_CONNECTIONS_QUEUE_SIZE = 5
	TIMEOUT = 0.25
	
	def __init__(self, af, address_for_binding="127.0.0.1"):
		self._kill_flag = False
		self._address_for_binding = address_for_binding

		self._UDP_sock = socket.socket(af, socket.SOCK_DGRAM)
		self._prepare_UDP_socket()
		self._UDP_receiving_thread = threading.Thread(target=self._receive_emulated_pings_over_UDP, args=())
		self._UDP_receiving_thread.start()

		self._TCP_sock = socket.socket(af, socket.SOCK_STREAM)
		self._prepare_TCP_socket()
		self._TCP_listening_thread = threading.Thread(target=self._accept_emulated_pings_over_TCP, args=())
		self._TCP_listening_thread.start()


	def _prepare_UDP_socket(self):
		self._UDP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._UDP_sock.settimeout(self.TIMEOUT)
		self._UDP_sock.bind((self._address_for_binding, self.SERVER_PORT))


	def _prepare_TCP_socket(self):
		self._TCP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._TCP_sock.settimeout(self.TIMEOUT)
		self._TCP_sock.bind((self._address_for_binding, self.SERVER_PORT))
		self._TCP_sock.listen(self.PENDING_CONNECTIONS_QUEUE_SIZE)


	def _receive_emulated_pings_over_UDP(self):
		while not self._kill_flag:
			try:
				received_data, ((msg_src_address, msg_src_port)) = self._UDP_sock.recvfrom(self.BUFFER_SIZE)
			except socket.timeout:
				continue # timeout lets us to re-estimate self._kill_flag every TIMEOUT seconds
			ping_packet = pickle.loads(received_data)
			if ping_packet.magic_number != self.REQUEST_MAGIC_NUMBER:
				print("Wrong magic number, probably not a ping message")
				continue
			ping_packet.magic_number = self.REPLY_MAGIC_NUMBER
			serialized_msg = pickle.dumps(ping_packet)
			bytes_sent = self._UDP_sock.sendto(serialized_msg, (msg_src_address, msg_src_port))
			if bytes_sent != len(serialized_msg):
				raise RuntimeError("An error occured while sending message over UDP socket:", bytes_sent, "out of", len(serialized_msg), "sent")


	def _accept_emulated_pings_over_TCP(self):
		while not self._kill_flag:
			try:
				self._TCP_sock.accept()
			except socket.timeout:
				continue # timeout lets us to re-estimate self._kill_flag every TIMEOUT seconds


	def terminate(self):
		self._kill_flag = True

		if self._UDP_receiving_thread:
			self._UDP_receiving_thread.join()
		if self._UDP_sock:
			self._UDP_sock.close()
		if self._TCP_listening_thread:
			self._TCP_listening_thread.join()
		if self._TCP_sock:
			self._TCP_sock.close()

