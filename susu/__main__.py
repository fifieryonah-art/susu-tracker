"""Run with python -m susu --help."""

import argparse
import json
import sys

from .errors import SusuError
from .group import SusuGroup
from .storage import load, save


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manage one rotating savings group (GHS).")
    parser.add_argument("--file", default="susu.json", help="state file (default: susu.json)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("create", help="create a group without overwriting existing data").add_argument("amount")
    commands.add_parser("add", help="add a member").add_argument("member")
    pay = commands.add_parser("pay", help="record a contribution")
    pay.add_argument("member")
    pay.add_argument("week", type=int)
    pay.add_argument("amount")
    commands.add_parser("close", help="attempt to close the current week")
    commands.add_parser("report", help="show balances and payout history")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            group = SusuGroup(args.amount)
            document = {"version": 1, "weekly_contribution": group.report()["weekly_contribution"], "events": []}
            save(args.file, document, create=True)
            print("Group created. Weekly contribution: GHS " + document["weekly_contribution"])
            return 0
        group, document = load(args.file)
        if args.command == "report":
            print(json.dumps(group.report(), indent=2, ensure_ascii=False))
            return 0
        if args.command == "add":
            group.add_member(args.member)
            event = {"action": "add", "member": args.member}
            message = f"Member added: {args.member.strip()}"
        elif args.command == "pay":
            group.record_contribution(args.member, args.week, args.amount)
            event = {"action": "pay", "member": args.member, "week": args.week, "amount": args.amount}
            message = f"Payment recorded for {args.member.strip()}, week {args.week}."
        else:
            result = group.close_week()
            if not result["closed"]:
                print(f"Week {group.current_week} cannot close.")
                for member, amount in result["owing"].items():
                    print(f"{member} owes {amount} GHS")
                return 1
            payout = result["payout"]
            event = {"action": "close"}
            message = f"Week {payout['week']} closed. {payout['member']} receives {payout['amount']} GHS."
        document["events"].append(event)
        save(args.file, document)
        print(message)
        return 0
    except SusuError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
