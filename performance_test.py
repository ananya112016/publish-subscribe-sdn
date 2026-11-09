import socket
import time
import statistics

HOST = "10.0.0.1"
PORT = 5000
COUNT = 100

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.settimeout(5)

latencies = []
total_start = time.perf_counter()

try:
    for i in range(COUNT):
        payload = f"PUBLISH|performance|message_{i}\n".encode()

        start = time.perf_counter()
        client.sendall(payload)

        response = b""
        while b"\n" not in response:
            chunk = client.recv(4096)
            if not chunk:
                raise ConnectionError("Broker closed the connection")
            response += chunk

        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    total_time = time.perf_counter() - total_start

    print("Messages acknowledged:", len(latencies))
    print(f"Average publisher-broker ACK latency: {statistics.mean(latencies):.3f} ms")
    print(f"Minimum ACK latency: {min(latencies):.3f} ms")
    print(f"Maximum ACK latency: {max(latencies):.3f} ms")
    print(f"Total time: {total_time:.3f} seconds")
    print(f"Acknowledged messages/sec: {len(latencies) / total_time:.2f}")

finally:
    client.close()
