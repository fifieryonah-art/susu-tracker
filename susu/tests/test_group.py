"""Group rules, including the example from the project brief."""

import unittest

from susu.errors import (
    CycleCompleteError, DuplicateMemberError, InvalidAmountError,
    InvalidMemberNameError, MembershipClosedError, NoMembersError,
    OverpaymentError, UnknownMemberError, WrongWeekError,
)
from susu.group import SusuGroup


class GroupTests(unittest.TestCase):
    def setUp(self):
        self.group = SusuGroup("50.00")
        for name in ("Ama", "Kofi", "Esi"):
            self.group.add_member(name)

    def pay_everyone(self):
        for name in ("Ama", "Kofi", "Esi"):
            self.group.record_contribution(name, self.group.current_week, "50")

    def test_partial_payments_and_blocked_closure(self):
        self.group.record_contribution("Ama", 1, "50")
        self.group.record_contribution("Kofi", 1, "50")
        self.group.record_contribution("Esi", 1, "30")
        before = self.group.report()
        result = self.group.close_week()
        self.assertFalse(result["closed"])
        self.assertEqual(result["owing"], {"Esi": "20.00"})
        self.assertIsNone(result["payout"])
        self.assertEqual(self.group.report(), before)
        self.assertEqual(before["paid_in_full"], ["Ama", "Kofi"])
        self.group.record_contribution("Esi", 1, "20")
        self.assertEqual(self.group.close_week()["payout"],
                         {"week": 1, "member": "Ama", "amount": "150.00"})
        report = self.group.report()
        self.assertEqual(report["current_week"], 2)
        self.assertEqual(report["next_recipient"], "Kofi")
        self.assertEqual(report["owing"], dict.fromkeys(("Ama", "Kofi", "Esi"), "50.00"))
        self.assertEqual(len(report["payout_history"]), 1)

    def test_payout_order_and_completion(self):
        for name in ("Ama", "Kofi", "Esi"):
            self.pay_everyone()
            self.assertEqual(self.group.close_week()["payout"]["member"], name)
        report = self.group.report()
        self.assertTrue(report["complete"])
        self.assertEqual(report["current_week"], 4)
        self.assertIsNone(report["next_recipient"])
        self.assertEqual(report["owing"], {})
        with self.assertRaises(CycleCompleteError):
            self.group.close_week()
        with self.assertRaises(CycleCompleteError):
            self.group.record_contribution("Ama", 4, "50")
        with self.assertRaises(CycleCompleteError):
            self.group.add_member("Yaw")

    def test_duplicate_and_invalid_members(self):
        with self.assertRaises(DuplicateMemberError):
            self.group.add_member(" Ama ")
        for name in ("", "  ", None, 42):
            with self.subTest(name=name), self.assertRaises(InvalidMemberNameError):
                self.group.add_member(name)

    def test_unknown_member(self):
        with self.assertRaises(UnknownMemberError):
            self.group.record_contribution("Yaw", 1, "50")

    def test_invalid_payment_does_not_change_state_or_lock_membership(self):
        before = self.group.report()
        for amount in ("0", "-5", "50.01", 0.1):
            with self.subTest(amount=amount):
                with self.assertRaises((InvalidAmountError, OverpaymentError)):
                    self.group.record_contribution("Ama", 1, amount)
                self.assertEqual(self.group.report(), before)
        self.group.add_member("Yaw")

    def test_rejects_overpayment_after_partial_payment(self):
        self.group.record_contribution("Ama", 1, "30")
        with self.assertRaises(OverpaymentError):
            self.group.record_contribution("Ama", 1, "20.01")
        self.assertEqual(self.group.report()["owing"]["Ama"], "20.00")

    def test_membership_locks_after_first_payment(self):
        self.group.record_contribution("Ama", 1, "0.01")
        with self.assertRaises(MembershipClosedError):
            self.group.add_member("Yaw")

    def test_rejects_wrong_weeks_and_boolean(self):
        for week in (0, 2, True, 1.0, "1"):
            with self.subTest(week=week), self.assertRaises(WrongWeekError):
                self.group.record_contribution("Ama", week, "50")
        self.pay_everyone()
        self.group.close_week()
        with self.assertRaises(WrongWeekError):
            self.group.record_contribution("Ama", 1, "50")

    def test_empty_group_cannot_close(self):
        with self.assertRaises(NoMembersError):
            SusuGroup("50").close_week()

    def test_invalid_weekly_contribution(self):
        for amount in ("0", "-1", "1.001", 50.0):
            with self.subTest(amount=amount), self.assertRaises(InvalidAmountError):
                SusuGroup(amount)

    def test_report_and_payout_are_independent_snapshots(self):
        self.pay_everyone()
        result = self.group.close_week()
        result["payout"]["amount"] = "0.00"
        report = self.group.report()
        report["members"].clear()
        report["owing"].clear()
        report["payout_history"][0]["member"] = "Changed"
        fresh = self.group.report()
        self.assertEqual(fresh["members"], ["Ama", "Kofi", "Esi"])
        self.assertEqual(fresh["payout_history"][0],
                         {"week": 1, "member": "Ama", "amount": "150.00"})
        self.assertEqual(len(fresh["owing"]), 3)

    def test_single_member_cycle(self):
        group = SusuGroup("0.01")
        group.add_member(" Solo ")
        group.record_contribution(" Solo ", 1, "0.01")
        self.assertEqual(group.close_week()["payout"]["amount"], "0.01")
        self.assertTrue(group.complete)


if __name__ == "__main__":
    unittest.main()
