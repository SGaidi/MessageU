# MessageU

A very basic E2E encrypted messaging app, made as part of defensive systems course in University.
It's a server-client model, in which clients can send files and messages to each other, and the server acts as an intermediate.
All messages stored in the server are encrypted, and there's a basic django admin support.

_Note that it's very primitive, and due to project requirements it's not robust._

## Prerequisites

- Python3.6 or higher.
- Windows or Linux OS.

## Installation

```sh
pip install -r requirements.txt
```

## Configuration

### Server

edit the `port.info` file with the port you want to have open for clients.

### Client

edit the `server.info` file with the hostname and port of the server machine.

## Running

### Server
```sh
python main.py server
```

While running, admin panel is available at `localhost:8000/admin`. Default credentials are `admin` and `admin`.

You will be able to see:

- Registered user and their public keys.
- Pending encrypted messages.

### Client

```sh
python main.py client
```

You will have a menu displaying possible actions.

The Fastest way to send a message to another client would be:

1. Register (1).
2. List clients (2). From the list find the client you wish to send a message to.
3. Send or receive a symmetric key (51 or 52).
4. Send a message (5).

A longer way to do this, is a step-by-step procedure:

1. Register.
2. List clients. Find another client.
3. Explicitly request the client's public key.
4. Send a symmetric key encrypted by the other client's public key.
5. Send a message or file, encrypted by a shared symmetric key.
6. Request for waiting messages, to see any responses.
