import socket

def get_free_port():
    """获取一个可用的本地端口号"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    _, port = sock.getsockname()
    sock.close()

    return port
