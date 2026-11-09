import socket
import time

HOST = "10.0.0.1"
PORT = 5000

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print("Connected to broker.")

    latencies = []
    total_bytes = 0

    try:
        while True:
            topic = input("Enter topic (or exit): ").strip()

            if topic.lower() == "exit":
                break

            message = input("Enter message: ").strip()
            payload = f"PUBLISH|{topic}|{message}\n".encode()

            start = time.perf_counter()
            client.sendall(payload)
            elapsed_ms = (time.perf_counter() - start) * 1000

            latencies.append(elapsed_ms)
            total_bytes += len(payload)

            print(f"Message sent. Send time: {elapsed_ms:.3f} ms")

    finally:
        client.close()

    if latencies:
        print("\n--- Performance Results ---")
        print(f"Messages sent: {len(latencies)}")
        print(f"Average send time: {sum(latencies) / len(latencies):.3f} ms")
        print(f"Total payload: {total_bytes} bytes")

if __name__ == "__main__":
    main()
