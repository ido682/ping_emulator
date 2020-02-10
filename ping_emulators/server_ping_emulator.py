import socket
import select
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
		self._TCP_sock = socket.socket(af, socket.SOCK_STREAM)
		self._prepare_TCP_socket()

		self._select_thread = threading.Thread(target=self._select, args=())
		self._select_thread.start()


	def _prepare_UDP_socket(self):
		self._UDP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._UDP_sock.setblocking(0)
		self._UDP_sock.bind((self._address_for_binding, self.SERVER_PORT))


	def _prepare_TCP_socket(self):
		self._TCP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._TCP_sock.setblocking(0)
		self._TCP_sock.bind((self._address_for_binding, self.SERVER_PORT))
		self._TCP_sock.listen(self.PENDING_CONNECTIONS_QUEUE_SIZE)


	def _select(self):
		while not self._kill_flag:
			sockets_for_reading = [self._UDP_sock, self._TCP_sock]
			readable, writable, exceptional = select.select(sockets_for_reading, [], [], self.TIMEOUT)
			for curr_sock in readable:
				if curr_sock is self._UDP_sock:
					self._receive_emulated_pings_over_UDP()
				if curr_sock is self._TCP_sock:
					self._TCP_sock.accept()


	def _receive_emulated_pings_over_UDP(self):
		received_data, (msg_src) = self._UDP_sock.recvfrom(self.BUFFER_SIZE)
		ping_packet = pickle.loads(received_data)
		if ping_packet.magic_number != self.REQUEST_MAGIC_NUMBER:
			print("Wrong magic number, probably not a ping message")
			return
		ping_packet.magic_number = self.REPLY_MAGIC_NUMBER
		serialized_msg = pickle.dumps(ping_packet)
		bytes_sent = self._UDP_sock.sendto(serialized_msg, msg_src)
		if bytes_sent != len(serialized_msg):
			raise RuntimeError("An error occured while sending message over UDP socket:", bytes_sent, "out of", len(serialized_msg), "sent")


	def terminate(self):
		self._kill_flag = True

		if self._select_thread:
			self._select_thread.join()
		if self._UDP_sock:
			self._UDP_sock.close()
		if self._TCP_sock:
			self._TCP_sock.close()

