# Demo script — what to say, what to type, what they see

**Total target:** 13 minutes. Each beat is ≈ 2 minutes; Beat 5 is a 30-second reveal; budget reserve at the end.

## Pre-flight (do this *before* you start talking)

In four terminal tabs, in order. Test the whole script the day before.

```
T1)  make up && make producer       # Kafka + synthetic orders flowing
T2)  make server                    # MCP server listening on :8000
T3)  make audit                     # audit viewer, empty so far
T4)  (leave empty — you'll run `make demo` here on stage)
```

Verify before you go on:
- T1 shows `producer: 10 orders sent…` every ~10s.
- T2 shows `FastMCP on http://127.0.0.1:8000/mcp` and `consuming 'orders' → order ledger`.
- T3 shows the audit-viewer banner with no events yet.

If you cannot trust Wi-Fi, set `OFFLINE_MODE=true` in `.env` *before* `make server`. Only Beat 6 is affected.

---

## On stage — the demo

Open T4. Say: *"The slide you just saw mapped governance concepts to MCP mechanisms. The next thirteen minutes is that slide, running."*

Run:
```
make demo
```

### Beat 1 — Read live data (≈90s)

What the audience sees: scripted client connects, calls `list_recent_orders` as `agent_basic`, returns five recent orders for `C001`.

What to say: *"Start simple. This is the agent reading from the live stream. The data wasn't here a minute ago — `make producer` is feeding it in real time. This is what Part 1 was about."*

Press Enter to advance.

### Beat 2 — Access control (≈90s)

What the audience sees: the same `agent_basic` identity calls `cancel_order` (tier 3). Server returns `{"ok": false, "denied": true, "reason": "identity 'agent_basic' not authorized for tier-3 tool 'cancel_order'"}`.

What to say: *"Notice **the model didn't decide this**. The server enforced it. The model has no idea what tier means — the tier table lives in `policy.yaml` and is read only by the server. The boundary is the trust boundary."*

Optional aside: open `src/governed_agents/policy.yaml` for ten seconds. Audience sees fifteen lines of YAML governing the whole system.

### Beat 3 — Shadow mode (≈90s)

What the audience sees: identity switches to `agent_advanced`. Same `cancel_order` call. Returns `{"ok": true, "mode": "shadow", "simulated": {"would_become_status": "cancelled", "would_refund_amount": ...}}`.

What to say: *"Same tool, different identity — now allowed. But look: the response says `mode: shadow`. The server didn't actually cancel anything. It computed what would happen, returned a response the agent can't distinguish from a real one, and logged it. **This is how you validate a high-risk agent capability in production traffic before turning execution on.**"*

### Beat 4 — Human-in-the-loop (≈3 min — biggest beat)

What the audience sees: agent calls `issue_refund`. Returns `{"status": "awaiting_approval", "approval_id": "A-XXXXXXXX"}`. The client starts polling: `poll 1: status=pending`, `poll 2: status=pending`…

What to say: *"Tier 4. This one needs a human. The agent is suspended — really suspended; the call is blocked on the server. I'm the human."*

Switch to T2 or a fifth terminal:
```
make approve ID=A-XXXXXXXX
```

The approver CLI prints the request, you type `y`. The polling client in T4 reports `status=approved`, automatically resumes, executes the refund. The audience hears the click.

What to say: *"That's human oversight as a code primitive — not a policy bullet, not a Slack message someone hopes someone else reads."*

### Beat 5 — Auditability (≈30s)

What the audience sees: you Alt-Tab to T3 (audit viewer). Five color-coded events are sitting there:
- `agent_basic` · `list_recent_orders` · ok
- `agent_basic` · `cancel_order` · **denied**
- `agent_advanced` · `cancel_order` · **shadow**
- `agent_advanced` · `issue_refund` · awaiting_approval
- `agent_advanced` · `issue_refund` · **executed** (with approver name)

What to say: *"Every beat you just saw produced a structured event on a Kafka topic — including the denied one and the shadow simulation. **The audit log is a stream.** That's the bridge back to Part 1: lineage was the data-layer property; this is the same primitive at the tool layer."*

Switch back to T4. Press Enter.

### Beat 6 — Multi-model routing (≈90s)

What the audience sees: `assess_fraud_risk` called for two customers. Result includes `model: "claude-haiku-..."` for one, `model: "claude-opus-..."` for the other, with `routing_reason: "risk_score=0.84 — escalate to flagship model"`.

What to say: *"Last beat. 'Scalable multi-model architecture' usually means a slide. Here it's a tool that decides which model by signal — and **logs the routing decision** to the audit topic. Model selection becomes auditable. The audience watching the dashboard tomorrow can answer 'why did we spend Opus tokens on customer C010?' in one query."*

---

## Close (≈30s)

Say: *"Six beats. Each one was a slide from the second half of the talk, running as the same MCP server you'd build in production. **The model never enforced anything. The server did.** That's the move: govern at the data layer and the tool layer, where you already know how to engineer."*

Pitch the repo: github.com/gajendra2k2/governed-agents-demo · MIT · one `make demo` away.

Hand off to Q&A.

---

## Failure-mode playbook

| If…                            | Do this                                          |
|--------------------------------|--------------------------------------------------|
| Kafka isn't up                 | `make down && make up`                           |
| Producer isn't running         | Beat 1 returns no orders → start `make producer` |
| Approval doesn't trigger       | Run `make approve ID=…` in any terminal          |
| Anthropic API fails on Beat 6  | Set `OFFLINE_MODE=true`, restart server          |
| Audience asks "what about X?"  | See `TALK.md` Q&A section                        |
