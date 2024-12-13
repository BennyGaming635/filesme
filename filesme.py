import socket
import os
import threading
import time
from tqdm import tqdm  # For progress bar

# Function to discover available devices on the local network
def discover_devices(port=5001, broadcast_interval=5):
    broadcast_address = '<broadcast>'  # Broadcast address
    discovered_devices = []  # List to store discovered devices

    # Create a UDP socket for broadcasting
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_socket.bind(('', port))

    # Send a broadcast message to all devices
    message = "DISCOVER_PEER"
    while True:
        server_socket.sendto(message.encode(), (broadcast_address, port))
        print(f"Broadcasting message: {message}")
        time.sleep(broadcast_interval)

        # Listen for responses
        data, addr = server_socket.recvfrom(1024)
        if data.decode() == "PEER_RESPONSE":
            if addr[0] not in discovered_devices:
                discovered_devices.append(addr[0])
                print(f"Peer found: {addr[0]}")

# Function to handle receiving files
def receive_files(client_socket):
    try:
        # Receive the number of files
        num_files = int(client_socket.recv(1024).decode())
        print(f"Receiving {num_files} files...")

        for _ in range(num_files):
            # Receive the file name
            file_name = client_socket.recv(1024).decode()
            print(f"Receiving file: {file_name}")

            # Open a file to write the received data
            with open(file_name, 'wb') as file:
                while True:
                    # Receive data in chunks
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)

            print(f"File {file_name} has been received successfully!")

    except Exception as e:
        print(f"Error occurred while receiving files: {e}")
    finally:
        client_socket.close()

# Function to handle sending files
def send_files(peer_ip, peer_port):
    try:
        # Create a socket and connect to peer
        client_socket = socket.socket()
        client_socket.connect((peer_ip, peer_port))

        # Get the list of files to send
        file_paths = input("Enter the full paths of the files to send (comma separated): ").split(',')
        file_paths = [path.strip() for path in file_paths]

        # Check if all files exist
        for path in file_paths:
            if not os.path.isfile(path):
                print(f"File not found: {path}")
                return

        # Send the number of files
        client_socket.send(str(len(file_paths)).encode())

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            client_socket.send(file_name.encode())  # Send file name

            # Open the file and send it in chunks
            with open(file_path, 'rb') as file:
                # Use tqdm for a progress bar
                file_size = os.path.getsize(file_path)
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    while True:
                        # Read a chunk of the file
                        data = file.read(1024)
                        if not data:
                            break
                        client_socket.send(data)  # Send chunk
                        pbar.update(len(data))  # Update progress bar

            print(f"File {file_name} has been sent successfully!")

    except Exception as e:
        print(f"Error occurred while sending files: {e}")
    finally:
        client_socket.close()

# Function to listen for incoming file transfers
def listen_for_files(port=5000):
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)

    print(f"Listening for incoming files on port {port}...")

    client_socket, address = server_socket.accept()
    print(f"Connection established with {address}")

    # Handle receiving files
    receive_files(client_socket)

# Main function to start the P2P file sharing and discovery
def p2p_file_sharing():
    # Discover devices in the local network
    discover_devices()

    # Ask the user to select a peer
    peer_ip = input("Enter the IP address of the peer to send files to: ")
    peer_port = 5000  # Default port to use

    # Start listening for incoming file transfers
    listen_thread = threading.Thread(target=listen_for_files, args=(peer_port,))
    listen_thread.start()

    # Allow a small delay for the listener to start
    print("Waiting for peer to connect...")
    threading.Event().wait(1)

    # Now send files to the selected peer
    send_files(peer_ip, peer_port)

if __name__ == "__main__":
    p2p_file_sharing()
