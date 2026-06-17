"""Approver CLI — the human in the loop.

Usage:  python scripts/approve.py <approval_id>
        (or:  make approve ID=<approval_id>)

Reads the pending approval from SQLite, shows you what the agent wants to do,
records your decision, and publishes it to the `approvals` Kafka topic so the
audit story stays streaming-native.
"""
from __future__ import annotations

import getpass
import sys

from rich.console import Console
from rich.panel import Panel

from governed_agents.server import approvals, state

console = Console()


def main() -> int:
    if len(sys.argv) != 2:
        console.print("[red]usage: python scripts/approve.py <approval_id>[/]")
        return 2
    approval_id = sys.argv[1]
    state.init_db()

    record = state.get_approval(approval_id)
    if record is None:
        console.print(f"[red]No such approval: {approval_id}[/]")
        return 1
    if record["status"] != "pending":
        console.print(f"[yellow]Already decided: status={record['status']}[/]")
        return 0

    console.print(Panel.fit(
        f"[bold]Approval request[/]\n"
        f"  id:       {approval_id}\n"
        f"  identity: [yellow]{record['identity']}[/]\n"
        f"  tool:     [cyan]{record['tool']}[/]\n"
        f"  args:     {record['args']}",
        border_style="magenta",
    ))
    choice = console.input("[bold]Approve? (y/N) [/]").strip().lower()
    decision = "approved" if choice in {"y", "yes"} else "rejected"
    approver = getpass.getuser()
    ok = approvals.decide(approval_id, decision, approver)
    if ok:
        console.print(f"[bold green]→ {decision} by {approver}[/]")
        return 0
    console.print("[red]race: another approver already decided[/]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
