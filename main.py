from core.connectors.pcl import PCLConnector
from core.easytier import EasyTier

if __name__ == "__main__":
    easytier = EasyTier()
    invite_code = input("请输入 PCL 邀请码: ").strip()
    if not PCLConnector.verify_invite_code(invite_code):
        print("无效的 PCL 邀请码格式！")
        exit(1)
    connector = PCLConnector(easytier, invite_code)
    connector.connect()
    while True:
        try:
            cmd = input("输入 'exit' 或按下 Ctrl+C 退出: ").strip()
            if cmd.lower() == 'exit':
                break
        except KeyboardInterrupt:
            break
    connector.disconnect()
