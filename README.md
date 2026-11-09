# Publish–Subscribe Messaging System using TCP and SDN

## 1. Project Overview

This project implements a TCP-based Publish–Subscribe Messaging System integrated with Software-Defined Networking (SDN).

The system allows publishers to send messages to a broker under specific topics. Subscribers subscribe to topics and receive messages published under those topics.

The project uses Python socket programming, Mininet, Open vSwitch and the OS-Ken SDN controller.

## 2. Technologies Used

- Python 3
- TCP Socket Programming
- Mininet
- Open vSwitch (OVS)
- OS-Ken SDN Controller
- OpenFlow 1.3
- Ubuntu Linux

## 3. System Architecture

The project uses a single-switch, two-host Mininet topology.

- **h1 (10.0.0.1):** Runs the message broker on TCP port 5000.
- **h2 (10.0.0.2):** Runs the publisher and subscriber clients.
- **s1:** Open vSwitch switch.
- **OS-Ken:** Controls the network through OpenFlow.

### Communication Flow

1. The publisher connects to the broker using TCP.
2. The subscriber connects to the broker and subscribes to a topic.
3. The publisher sends a message under a topic.
4. The broker forwards the message to all subscribers registered for that topic.
5. The SDN controller manages network forwarding and dynamic traffic policies.

## 4. Project Files

| File | Description |
|---|---|
| `broker.py` | TCP broker that manages client connections and message delivery |
| `publisher.py` | Publisher client that sends topic-based messages |
| `subscriber.py` | Subscriber client that subscribes to topics and receives messages |
| `sdn_controller_d2.py` | OS-Ken SDN controller with dynamic BLOCK/ALLOW policies |
| `performance_test.py` | Measures broker acknowledgement latency and throughput |
| `d2_policy.txt` | Stores the current SDN traffic policy |

## 5. Setup Requirements

Run the project in an Ubuntu environment with Python 3, Mininet, Open vSwitch and OS-Ken installed.

Activate the OS-Ken virtual environment:

```bash
source ~/publish-subscribe-sdn/osken-env/bin/activate
```

## 6. Running the Project

### Step 1: Start the SDN Controller

Navigate to the D2 project directory:

```bash
cd ~/publish-subscribe-sdn-D2
```

Start the controller:

```bash
osken-manager sdn_controller_d2.py
```

Keep this terminal running.

### Step 2: Start Mininet

Open another terminal and clean up any previous topology:

```bash
sudo mn -c
```

Start the Mininet topology:

```bash
sudo mn --switch ovsk --topo single,2 --controller remote,ip=127.0.0.1,port=6653 --mac
```

Test connectivity:

```bash
pingall
```

### Step 3: Start the Broker

At the Mininet prompt:

```bash
h1 python3 /tmp/ps-project/broker.py &
```

### Step 4: Start a Subscriber

```bash
h2 python3 /tmp/ps-project/subscriber.py
```

Subscribe to a topic:

```text
subscribe sports
```

### Step 5: Start a Publisher

Open another Ubuntu terminal:

```bash
sudo mnexec -a $(pgrep -f 'mininet:h2' | head -1) python3 /tmp/ps-project/publisher.py
```

Enter the topic and message when prompted.

The broker delivers the message to subscribers registered for that topic.

## 7. Dynamic SDN Functionality

The D2 controller supports dynamic traffic policies using `d2_policy.txt`.

### BLOCK Policy

Set the policy to BLOCK:

```bash
echo BLOCK > ~/publish-subscribe-sdn-D2/d2_policy.txt
```

The controller installs high-priority OpenFlow DROP rules for TCP traffic associated with broker port 5000.

### ALLOW Policy

Set the policy to ALLOW:

```bash
echo ALLOW > ~/publish-subscribe-sdn-D2/d2_policy.txt
```

The controller removes the policy DROP rules and restores normal forwarding.

### Verify Flow Rules

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

The BLOCK policy uses priority-200 DROP rules, while normal broker forwarding rules use priority 100.

**Note:** The demonstrated policy switching is manually triggered through the policy file. The rules block broker TCP traffic as a whole and do not distinguish individual application topics.

## 8. Performance Evaluation

The performance testing script sends 100 messages per run and measures:

- Average publisher-to-broker acknowledgement latency
- Minimum acknowledgement latency
- Maximum acknowledgement latency
- Total execution time
- Acknowledged messages per second

Three runs were performed for each configuration.

### Performance Comparison

| Metric | Baseline | SDN |
|---|---:|---:|
| Average ACK latency | 0.4173 ms | 0.0963 ms |
| Average throughput | 3,127.55 msg/s | 15,026.58 msg/s |
| Total messages acknowledged | 300 | 300 |

The measured SDN configuration showed approximately 76.9% lower average acknowledgement latency and 4.8 times higher average throughput in the conducted experiments.

These measurements represent broker acknowledgements, not end-to-end subscriber delivery latency.

## 9. Testing and Robustness

The following tests were performed:

1. Mininet host connectivity using `pingall`.
2. Publisher-to-broker TCP communication.
3. Subscriber topic subscription.
4. Message delivery to multiple subscribers.
5. Dynamic SDN traffic blocking using BLOCK.
6. Traffic restoration using ALLOW.
7. Broker failure simulation by terminating the broker process.
8. Broker restart and successful subscriber reconnection.
9. Message delivery verification after broker recovery.
10. Performance evaluation under baseline and SDN-controlled configurations.

## 10. Conclusion

The project demonstrates a TCP-based publish–subscribe messaging application integrated with a programmable SDN network.

The application supports topic-based communication, multiple subscribers, and broker-mediated message delivery. The OS-Ken controller demonstrates dynamic traffic blocking and restoration using OpenFlow rules.

Performance measurements and robustness experiments were conducted to evaluate the system under different conditions.

## 11. Authors

- Student Name: [Enter name]
- USN: [Enter USN]
- Institution: PES University, Bengaluru

## 12. Repository Contents

This repository contains the source code, SDN controller implementation, policy configuration, performance testing script, project report and experimental evidence.
