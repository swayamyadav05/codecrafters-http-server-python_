import socket
import threading
import sys
import os


def main():
    def handle_req(client, addr):
        data = client.recv(1024).decode()
        if not data:
            client.close()
            return

        parts = data.split('\r\n\r\n', 1)
        headers_part = parts[0]
        body = parts[1] if len(parts) > 1 else ''

        headers = headers_part.split('\r\n')
        if not headers:
            client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client.close()
            return

        request_line = headers[0].split()
        if len(request_line) < 3:
            client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client.close()
            return

        method, path, _ = request_line
        headers_dict = {}
        for header in headers[1:]:
            if ': ' in header:
                key, value = header.split(': ', 1)
                headers_dict[key.lower()] = value

        response = b""
        if path == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"
        elif path.startswith("/echo/"):
            content = path[len("/echo/"):]
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content)}\r\n\r\n{content}".encode()
        elif path == "/user-agent":
            user_agent = headers_dict.get('user-agent', '')
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}".encode()
        elif method == "GET" and path.startswith("/files/"):
            directory = sys.argv[2]
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n{content}".encode()
            except Exception:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"
        elif method == "POST" and path.startswith("/files/"):
            if 'content-length' not in headers_dict:
                response = b"HTTP/1.1 400 Bad Request\r\n\r\n"
            else:
                directory = sys.argv[2]
                filename = path[len("/files/"):]
                content_length = int(headers_dict['content-length'])
                body_content = body[:content_length]
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, "w") as f:
                        f.write(body_content)
                    response = b"HTTP/1.1 201 Created\r\n\r\n"
                except Exception:
                    response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"
        else:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"

        client.send(response)
        client.close()

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client, addr = server_socket.accept()
        threading.Thread(target=handle_req, args=(client, addr)).start()


if __name__ == "__main__":
    main()