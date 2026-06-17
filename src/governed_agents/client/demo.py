"""Scripted demo client — walks the six beats live, in order.

The script is deterministic: identities, prompts, and pauses are fixed so the
demo runs the same way every time. It uses FastMCP's HTTP client so the
audience sees actual MCP tool calls hitting the governance layer.

Drive it from a third terminal:
    1) `make up && make producer`   (terminal 1 — Kafka + order stream)
    2) `make server`                (terminal 2 — MCP server)
    3) `make demo`                  (terminal 3 — this client)
    4) `make audit`                 (optional terminal 4 — audit viewer)
"""
from __future__ import annotations

import asyncio
import json
import time

from fastmcp import Client
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from ..config import SETTINGS

console = Console()
SERVER_URL = f"http://{SETTINGS.mcp_host}:{SETTINGS.mcp_port}/mcp/"


def banner(beat: str, identity: str, headline: str) -> None:
    console.print(Rule(f"[bold cyan]{beat}[/]  ·  identity=[bold yellow]{identity}[/]  ·  {headline}"))


def show_result(label: str, payload) -> None:
    if hasattr(payload, "data"):
        payload = payload.data
    text = json.dumps(payload, indent=2, default=str)
    console.print(Panel.fit(text, title=label, border_style="dim"))


def pause(prompt: str = "Press Enter for the next beat… ") -> None:
    try:
        input(prompt)
    except EOFError:
        time.sleep(1.0)


async def beat1(client: Client) -> dict:
    banner("BEAT 1 — Read live data", "agent_basic", "agent acts on the stream")
    res = await client.call_tool("list_recent_orders", {"identity": "agent_basic", "customer_id": "C001"})
    show_result("list_recent_orders → ok", res)
    pause()
    return res.data if hasattr(res, "data") else res


async def beat2(client: Client) -> None:
    banner("BEAT 2 — Access control", "agent_basic", "server denies a tier-3 tool")
    res = await client.call_tool(
        "cancel_order",
        {"identity": "agent_basic", "order_id": "O-DOESNTMATTER", "reason": "test"},
    )
    show_result("cancel_order → DENIED by server (not by model)", res)
    pause()


async def beat3(client: Client, sample_order_id: str) -> None:
    banner("BEAT 3 — Shadow mode", "agent_advanced", "high-risk write simulates + logs")
    res = await client.call_tool(
        "cancel_order",
        {"identity": "agent_advanced", "order_id": sample_order_id, "reason": "customer changed mind"},
    )
    show_result("cancel_order → shadow (no real cancellation, agent can't tell)", res)
    pause()


async def beat4(client: Client, sample_order_id: str) -> None:
    banner("BEAT 4 — Human-in-the-loop", "agent_advanced", "approval-gated refund")

    res1 = await client.call_tool(
        "issue_refund",
        {"identity": "agent_advanced", "order_id": sample_order_id, "amount": 49.99},
    )
    show_result("issue_refund → awaiting_approval", res1)
    approval_id = (res1.data if hasattr(res1, "data") else res1)["approval_id"]
    console.print(f"\n[bold magenta]>>> In another terminal:[/]  [bold]make approve ID={approval_id}[/]\n")

    for i in range(60):
        await asyncio.sleep(2)
        st = await client.call_tool("check_approval", {"identity": "agent_advanced", "approval_id": approval_id})
        status = (st.data if hasattr(st, "data") else st).get("status")
        console.print(f"  [dim]poll {i + 1}: status={status}[/]")
        if status in {"approved", "rejected"}:
            break
    else:
        console.print("[red]timed out waiting for approval — skipping execute[/]")
        return

    res2 = await client.call_tool(
        "issue_refund",
        {
            "identity": "agent_advanced",
            "order_id": sample_order_id,
            "amount": 49.99,
            "approval_id": approval_id,
        },
    )
    show_result("issue_refund (resumed with approval_id) → executed", res2)
    pause()


async def beat5() -> None:
    banner("BEAT 5 — Auditability", "ops", "switch to the audit-viewer terminal")
    console.print(
        "[bold]Open the audit-viewer terminal you started with `make audit`.[/]\n"
        "Every beat above produced a structured event on the [cyan]audit[/] Kafka topic:\n"
        "  identity · tool · tier · outcome · args · result\n"
        "That stream IS the lineage primitive from Part 1 of the talk — same idea,\n"
        "now applied to agent actions instead of business data.\n"
    )
    pause()


async def beat6(client: Client) -> None:
    banner("BEAT 6 — Multi-model routing", "agent_advanced", "right model for the risk")
    for cid in ("C001", "C010"):
        res = await client.call_tool("assess_fraud_risk", {"identity": "agent_advanced", "customer_id": cid})
        show_result(f"assess_fraud_risk({cid})", res)
    console.print(
        "[dim]Routing decision is logged on the audit topic alongside the result —\n"
        "model selection becomes auditable, not magic.[/]"
    )


async def run() -> None:
    console.print(Panel.fit(
        "[bold]Governed Agents — Live Demo[/]\n"
        "Six beats. Each one re-runs a slide from Part 2/3 of the talk as real code.\n"
        f"MCP server: [cyan]{SERVER_URL}[/]   ·   offline_mode=[yellow]{SETTINGS.offline_mode}[/]",
        border_style="cyan",
    ))
    pause("Press Enter to start Beat 1… ")

    async with Client(SERVER_URL) as client:
        first = await beat1(client)
        orders = first.get("orders", [])
        if not orders:
            console.print("[red]No orders found yet — start the producer (`make producer`) and rerun.[/]")
            return
        sample_order_id = orders[0]["order_id"]

        await beat2(client)
        await beat3(client, sample_order_id)
        await beat4(client, sample_order_id)
        await beat5()
        await beat6(client)

    console.print(Rule("[bold green]Demo complete[/]"))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
