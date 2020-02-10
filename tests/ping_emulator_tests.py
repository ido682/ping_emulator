import sys
import subprocess
import socket
import time

sys.path.append("..")

from ping_emulators.client_ping_emulator import ClientPingEmulator
from ping_emulators.server_ping_emulator import ServerPingEmulator
from ping_emulators.i_ping_emulator import IPingEmulator


DUMMY = "dummy"
BASE_ADDRESS_PREFIX = "192.168.111."
NETMASK_BITS = 24


##### WRAPPERS FOR TEST #####

class UDPClient(ClientPingEmulator):

	def __init__(self, address_for_binding="127.0.0.1"):
		super().__init__(socket.AF_INET, socket.SOCK_DGRAM, 1, address_for_binding)


class TCPClient(ClientPingEmulator):

	def __init__(self, address_for_binding="127.0.0.1"):
		super().__init__(socket.AF_INET, socket.SOCK_STREAM, 1, address_for_binding)


class Server(ServerPingEmulator):
	def __init__(self, address_for_binding="127.0.0.1"):
		super().__init__(socket.AF_INET, address_for_binding)


##### AUX FUNCTIONS FOR TEST #####

def get_address_by_iface_num(iface_num, should_add_netmask_bits=False):
	address = BASE_ADDRESS_PREFIX + str(iface_num)
	if should_add_netmask_bits:
		address += "/" + str(NETMASK_BITS)
	return address


def create_dummy_ifaces(ifname, num_of_ifaces):
	subprocess.run(["modprobe", DUMMY])
	subprocess.run(["ip", "link", "add", ifname, "type", DUMMY], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	for i in range(1, num_of_ifaces + 1):
		expanded_ifname = ifname + ":" + str(i)
		address = get_address_by_iface_num(i, should_add_netmask_bits=True)
		subprocess.run(["ip", "addr", "add", address, "brd", "+", "dev", ifname, "label", expanded_ifname])
	print("Dummy interfaces created")


def remove_dummy_ifaces(ifname):
	expanded_ifname = ifname + ":" + str(1)
	address = get_address_by_iface_num(1, should_add_netmask_bits=True)
	subprocess.run(["ip", "addr", "del", address, "dev", ifname, "label", expanded_ifname])

	subprocess.run(["ip", "link", "del", ifname, "type", DUMMY])
	subprocess.run(["rmmod", DUMMY])
	print("\nDummy interfaces removed\n")


def test_ping_emulators():
	iface_name = "iface_mock"
	num_of_ifaces = 4

	create_dummy_ifaces(iface_name, num_of_ifaces)
	run_all_tests()
	remove_dummy_ifaces(iface_name)


def run_all_tests():
	test_functions =[(test_one_UDP_client_no_server_plus_timeout_check,
					 "test_one_UDP_client_no_server_plus_timeout_check"),
					 (test_one_TCP_client_no_server,
					 "test_one_TCP_client_no_server"),
					 (test_one_UDP_client_with_one_server,
					 "test_one_UDP_client_with_one_server"),
					 (test_one_TCP_client_with_one_server,
					 "test_one_TCP_client_with_one_server"),
					 (test_one_UDP_client_with_one_server_two_pings,
					 "test_one_UDP_client_with_one_server_two_pings"),
					 (test_one_TCP_client_with_one_server_two_pings,
					 "test_one_TCP_client_with_one_server_two_pings"),
					 (test_one_UDP_client_with_one_server_wrong_address,
					 "test_one_UDP_client_with_one_server_wrong_address"),
					 (test_one_TCP_client_with_one_server_wrong_address,
					 "test_one_TCP_client_with_one_server_wrong_address"),
					 (test_one_UDP_client_with_two_servers,
					 "test_one_UDP_client_with_two_servers"),
					 (test_one_TCP_client_with_two_servers,
					 "test_one_TCP_client_with_two_servers"),
					 (test_two_UDP_client_with_one_server,
					 "test_two_UDP_client_with_one_server"),
					 (test_two_TCP_client_with_one_server,
					 "test_two_TCP_client_with_one_server"),
					 (test_UDP_and_TCP_clients_with_one_server,
					 "test_UDP_and_TCP_clients_with_one_server"),
					 (test_clients_trying_to_ping_each_other,
					 "test_clients_trying_to_ping_each_other")]
	
	errors = 0
	overall = 0

	for func, name in test_functions:
		overall += 1
		print("\nRunning", name)
		if not func():
			errors += 1
			print("********** WRONG **********")
		else:
			print("OK!")

	print("\nTested", overall, "functions, had", errors, "errors")


##### TEST FUNCTIONS #####

def test_one_UDP_client_no_server_plus_timeout_check():
	TIMEOUT = 1
	udp_client = UDPClient(get_address_by_iface_num(1))
	expected_ping_result = False
	time_before_ping = time.time()
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	time_after_ping = time.time()
	if expected_ping_result != actual_ping_result:
		return False

	time_difference = time_after_ping - time_before_ping
	expected_is_more_than_timeout = True
	actual_is_more_than_timeout = time_difference > TIMEOUT
	if expected_is_more_than_timeout != actual_is_more_than_timeout:
		return False

	return True


def test_one_TCP_client_no_server():
	tcp_client = TCPClient(get_address_by_iface_num(1))
	expected_ping_result = False
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		return False

	return True


def test_one_UDP_client_with_one_server():
	udp_client = UDPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	
	server.terminate()
	return True


def test_one_TCP_client_with_one_server():
	tcp_client = TCPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_one_UDP_client_with_one_server_two_pings():
	udp_client = UDPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_one_TCP_client_with_one_server_two_pings():
	tcp_client = TCPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_one_UDP_client_with_one_server_wrong_address():
	udp_client = UDPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = False
	actual_ping_result = udp_client.ping(get_address_by_iface_num(3))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_one_TCP_client_with_one_server_wrong_address():
	tcp_client = TCPClient(get_address_by_iface_num(1))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = False
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(3))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_one_UDP_client_with_two_servers():
	udp_client = UDPClient(get_address_by_iface_num(4))
	server1 = Server(get_address_by_iface_num(1))
	server2 = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server1.terminate()
		server2.terminate()
		return False
	actual_ping_result = udp_client.ping(get_address_by_iface_num(1))
	if expected_ping_result != actual_ping_result:
		server1.terminate()
		server2.terminate()
		return False
	
	server1.terminate()
	server2.terminate()
	return True


def test_one_TCP_client_with_two_servers():
	tcp_client = TCPClient(get_address_by_iface_num(4))
	server1 = Server(get_address_by_iface_num(1))
	server2 = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server1.terminate()
		server2.terminate()
		return False
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(1))
	if expected_ping_result != actual_ping_result:
		server1.terminate()
		server2.terminate()
		return False

	server1.terminate()
	server2.terminate()
	return True


def test_two_UDP_client_with_one_server():
	udp_client1 = UDPClient(get_address_by_iface_num(1))
	udp_client2 = UDPClient(get_address_by_iface_num(2))
	server = Server(get_address_by_iface_num(4))
	expected_ping_result = True
	actual_ping_result = udp_client1.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = udp_client2.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = udp_client1.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_two_TCP_client_with_one_server():
	tcp_client1 = TCPClient(get_address_by_iface_num(1))
	tcp_client2 = TCPClient(get_address_by_iface_num(2))
	server = Server(get_address_by_iface_num(4))
	expected_ping_result = True
	actual_ping_result = tcp_client1.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = tcp_client2.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = tcp_client2.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_UDP_and_TCP_clients_with_one_server():
	tcp_client = TCPClient(get_address_by_iface_num(3))
	udp_client = TCPClient(get_address_by_iface_num(4))
	server = Server(get_address_by_iface_num(2))
	expected_ping_result = True
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = udp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False
	actual_ping_result = tcp_client.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		server.terminate()
		return False

	server.terminate()
	return True


def test_clients_trying_to_ping_each_other():
	tcp_client1 = TCPClient(get_address_by_iface_num(1))
	tcp_client2 = TCPClient(get_address_by_iface_num(2))
	udp_client3 = TCPClient(get_address_by_iface_num(3))
	udp_client4 = TCPClient(get_address_by_iface_num(4))
	expected_ping_result = False
	actual_ping_result = tcp_client1.ping(get_address_by_iface_num(2))
	if expected_ping_result != actual_ping_result:
		return False
	actual_ping_result = udp_client3.ping(get_address_by_iface_num(4))
	if expected_ping_result != actual_ping_result:
		return False
	actual_ping_result = udp_client4.ping(get_address_by_iface_num(1))
	if expected_ping_result != actual_ping_result:
		return False
	
	return True
	

if __name__ == "__main__":
	test_ping_emulators()

