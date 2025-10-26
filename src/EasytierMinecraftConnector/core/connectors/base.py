from ..easytier import EasyTier

class EasyTierConnector:
    def __init__(self, easytier: EasyTier, invite_code: str, ):
        self.invite_code = invite_code.upper()
        self.easytier = easytier
        self.connected = False

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

class InvalidInviteCodeError(Exception):
    pass