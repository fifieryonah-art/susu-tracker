"""Business rules for one rotating savings cycle."""

from .errors import (
    CycleCompleteError, DuplicateMemberError, InvalidMemberNameError,
    MembershipClosedError, NoMembersError, OverpaymentError,
    UnknownMemberError, WrongWeekError,
)
from .money import format_amount, parse_amount


class SusuGroup:
    """Manage contributions in integer pesewas; reports use GHS strings."""

    def __init__(self, weekly_contribution):
        self._weekly_contribution = parse_amount(weekly_contribution)
        self._members = []
        self._payments = {}
        self._history = []
        self._current_week = 1
        self._started = False

    @property
    def current_week(self):
        return self._current_week

    @property
    def complete(self):
        return bool(self._members) and len(self._history) == len(self._members)

    def _require_active(self):
        if self.complete:
            raise CycleCompleteError("Every member has received a payout.")

    @staticmethod
    def _member_name(name):
        if not isinstance(name, str) or not name.strip():
            raise InvalidMemberNameError("Member names must be nonempty text.")
        return name.strip()

    def add_member(self, name):
        """Add a unique, case-sensitive name before the first accepted payment."""
        self._require_active()
        if self._started:
            raise MembershipClosedError("Membership closed with the first payment.")
        name = self._member_name(name)
        if name in self._payments:
            raise DuplicateMemberError(f"Member already exists: {name}")
        self._members.append(name)
        self._payments[name] = 0

    def record_contribution(self, member, week, amount):
        """Record a positive GHS payment for the current week only."""
        self._require_active()
        member = self._member_name(member)
        if member not in self._payments:
            raise UnknownMemberError(f"Unknown member: {member}")
        if type(week) is not int or week != self._current_week:
            raise WrongWeekError(f"Payments must target week {self._current_week}.")
        payment = parse_amount(amount)
        owed = self._weekly_contribution - self._payments[member]
        if payment > owed:
            raise OverpaymentError(f"{member} owes only GHS {format_amount(owed)}.")
        self._payments[member] += payment
        self._started = True

    def close_week(self):
        """Return a payout, or outstanding GHS balances without changing state."""
        self._require_active()
        if not self._members:
            raise NoMembersError("Add members before closing a week.")
        owing = self.report()["owing"]
        if owing:
            return {"closed": False, "owing": owing, "payout": None}
        payout = {
            "week": self._current_week,
            "member": self._members[len(self._history)],
            "amount": format_amount(self._weekly_contribution * len(self._members)),
        }
        self._history.append(payout)
        self._current_week += 1
        self._payments = dict.fromkeys(self._members, 0)
        return {"closed": True, "owing": {}, "payout": dict(payout)}

    def report(self):
        """Return an independent snapshot; all monetary strings are in GHS."""
        active = not self.complete
        return {
            "current_week": self._current_week,
            "complete": self.complete,
            "weekly_contribution": format_amount(self._weekly_contribution),
            "members": list(self._members),
            "next_recipient": self._members[len(self._history)]
            if self._members and active else None,
            "paid_in_full": [name for name in self._members
                             if active and self._payments[name] == self._weekly_contribution],
            "owing": {name: format_amount(self._weekly_contribution - self._payments[name])
                      for name in self._members
                      if active and self._payments[name] < self._weekly_contribution},
            "payout_history": [dict(payout) for payout in self._history],
        }
