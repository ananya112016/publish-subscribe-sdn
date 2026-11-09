import socket
import threading

HOST = "10.0.0.1"
PORT = 5000

def receive_messages(client):
    buffer = ""
    try:
        while True:
            data = client.recv(4096)
            if not data:
                break
            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line:
                    print(f"\n{line}")
                    print("Command (subscribe topic / unsubscribe topic / exit): ", end="", flush=True)
    except OSError:
        pass

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print("Connected to broker.")

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    try:
        while True:
            command = input("Command (subscribe topic / unsubscribe topic / exit): ").strip()
            parts = command.split(maxsplit=1)

            if len(parts) == 2 and parts[0].lower() == "subscribe":
                client.sendall(f"SUBSCRIBE|{parts[1]}\n".encode())
            elif len(parts) == 2 and parts[0].lower() == "unsubscribe":
                client.sendall(f"UNSUBSCRIBE|{parts[1]}\n".encode())
            elif command.lower() == "exit":
                break
            else:
                print("Use: subscribe sports")
    except (KeyboardInterrupt, OSError):
        pass
    finally:
        client.close()
        print("Subscriber disconnected.")

if __name__ == "__main__":
    main()
