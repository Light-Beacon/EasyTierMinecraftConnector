from ..easytier import EasyTier

class EasyTierConnector:
    def __init__(self, easytier: EasyTier, invite_code: str, ):
        self.invite_code = invite_code.upper()
        self.easytier = easytier
        self.connected = False

    def connect(self):
        print("Connecting to EasyTier with invite code:", self.invite_code)

class InvalidInviteCodeError(Exception):
    pass