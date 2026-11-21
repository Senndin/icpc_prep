"""Відкриває застосунок у браузері, щойно сервер почне приймати з'єднання."""
import socket
import time
import webbrowser

HOST, PORT = "127.0.0.1", 8000


def main():
    """Чекає до 60 секунд на запуск сервера та відкриває сторінку."""
    for _ in range(120):
        try:
            socket.create_connection((HOST, PORT), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        return
    webbrowser.open(f"http://{HOST}:{PORT}/")


if __name__ == "__main__":
    main()
