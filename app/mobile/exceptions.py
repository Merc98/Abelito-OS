class MobileAgentError(Exception):
    pass


class PermissionDeniedError(MobileAgentError):
    pass


class KillSwitchError(MobileAgentError):
    pass


class ParsingError(MobileAgentError):
    pass
