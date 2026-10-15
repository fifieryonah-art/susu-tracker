"""All validation failures raised by the susu package derive from SusuError."""


class SusuError(Exception):
    """Base class for every rule violation."""


class InvalidAmountError(SusuError):
    """An amount is invalid for a contribution or group setting."""


class InvalidMemberNameError(SusuError):
    """A member name does not meet the naming rules."""


class DuplicateMemberError(SusuError):
    """A member with this name or ID already exists."""


class UnknownMemberError(SusuError):
    """The requested member does not belong to the group."""


class MembershipClosedError(SusuError):
    """Members can no longer be added (the group has started)."""


class OverpaymentError(SusuError):
    """A payment exceeds the member's outstanding weekly contribution."""


class WrongWeekError(SusuError):
    """An operation targets a week that is not the current week."""


class NoMembersError(SusuError):
    """An operation requires members, but the group is empty."""


class CycleCompleteError(SusuError):
    """Every member has already received the pot; there is nothing left to do."""


class StateFileError(SusuError):
    """The saved group state cannot be read, validated, or written."""
