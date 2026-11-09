
import socket
import threading

HOST = "0.0.0.0"
PORT = 5000
subscribers = {}
clients = set()
lock = threading.Lock()

def handle_client(conn, addr):
    print(f"Connected: {addr}")
    topics = set()
    buffer = ""

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line:
                    continue

                parts = line.split("|", 2)
                command = parts[0]

                if command == "SUBSCRIBE" and len(parts) >= 2:
                    topic = parts[1]

                    with lock:
                        subscribers.setdefault(topic, set()).add(conn)
                        topics.add(topic)

                    conn.sendall(f"SUBSCRIBED|{topic}\n".encode())

                elif command == "UNSUBSCRIBE" and len(parts) >= 2:
                    topic = parts[1]

                    with lock:
                        subscribers.get(topic, set()).discard(conn)
                        topics.discard(topic)

                    conn.sendall(f"UNSUBSCRIBED|{topic}\n".encode())

                elif command == "PUBLISH" and len(parts) == 3:
                    topic, message = parts[1], parts[2]
                    payload = f"MESSAGE|{topic}|{message}\n".encode()

                    with lock:
                        targets = list(subscribers.get(topic, set()))

                    delivered = 0

                    for target in targets:
                        try:
                            target.sendall(payload)
                            delivered += 1
                        except OSError:
                            pass

                    conn.sendall(
                        f"ACK|{topic}|{delivered}\n".encode()
                    )

                    print(
                        f"Topic={topic}, "
                        f"delivered to {delivered} subscriber(s)"
                    )

                elif command == "QUIT":
                    return

    except (ConnectionError, OSError, UnicodeDecodeError):
        pass

    finally:
        with lock:
            for topic in topics:
                subscribers.get(topic, set()).discard(conn)

            clients.discard(conn)

        conn.close()
        print(f"Disconnected: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Broker listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()

            with lock:
                clients.add(conn)

            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\nBroker shutting down.")

    finally:
        server.close()

if __name__ == "__main__":
    main()
    
