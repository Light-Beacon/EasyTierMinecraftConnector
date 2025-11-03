import re
import random
from ..easytier import EasyTier
from .base import EasyTierConnector, InvalidInviteCodeError
from ..utils.freeport import get_free_port

class PCLConnector(EasyTierConnector):

    __PATTERN = re.compile(r'^[\[【]?(P([\dA-F]{4})-[\w\d]{5})-([\w\d]{5})[\]】]?$')

    @classmethod
    def verify_invite_code(cls, invite_code: str) -> bool:
        invite_code = invite_code.upper()
        return re.match(cls.__PATTERN, invite_code) is not None
    
    def __init__(self, easytier: EasyTier, invite_code: str):
        invite_code = invite_code.upper().replace('O', '0').replace('I','1')
        super().__init__(easytier, invite_code)
        matchobj = re.match(self.__PATTERN, self.invite_code)
        if matchobj is None:
            raise InvalidInviteCodeError()
        network_name, port_code, secret = matchobj.groups()
        self.network_name = network_name
        self.port = int('0x' + port_code, 16)
        self.secret = secret
        print(f"连接协议：PCL 协议\n网络名称: {self.network_name}, 端口: {self.port}, 密钥: {self.secret}")

    def connect(self):
        arguments = [
            "-d",
            "-p",
            "tcp://public2.easytier.cn:54321",
            "-p",
            "tcp://101.42.154.32:55558",
            "-p",
            "tcp://turn.hn.629957.xyz:14443",
            "-p",
            "tcp://119.45.189.143:11010",
            "--encryption-algorithm=chacha20",
            "--enable-kcp-proxy",
            "--use-smoltcp",
            "--no-tun",
            "--compression=zstd",
            "--multi-thread",
            "--latency-first",
            f"--network-name={self.network_name}",
            f"--network-secret={self.secret}",
            f"--hostname=Client-{random.randint(1000,9999)}",
        ]
        self.easytier.start_core(arguments)
        self.connected = True
        print(f"已通过 PCL 协议连接到 EasyTier 网络 {self.network_name}！")
        available_port = get_free_port()
        self.easytier.add_port_forwarding("tcp", f"127.0.0.1:{available_port}", f"10.114.114.114:{self.port}")
        self.easytier.add_port_forwarding("udp", f"127.0.0.1:{available_port}", f"10.114.114.114:{self.port}")
        self.easytier.add_port_forwarding("tcp", f"[::1]:{available_port}", f"10.114.114.114:{self.port}")
        self.easytier.add_port_forwarding("udp", f"[::1]:{available_port}", f"10.114.114.114:{self.port}")
        print(f"请使用地址：127.0.0.1:{available_port} 加入游戏！")

    def disconnect(self):
        if self.connected:
            self.easytier.stop_core()
            self.connected = False
            print("已断开 PCL 连接。")
        else:
            print("当前未连接，无需断开。")
