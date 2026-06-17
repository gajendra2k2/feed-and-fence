# Talk outline — slide ↔ demo mapping

**Title:** Feeding the Agents — and Fencing Them: Engineering Governed Agentic Systems on Real-Time Data
**Throughline:** *"An agent is only as good as the data you feed it and the fences you give it — and both are infrastructure you engineer, not features you bolt on."*
**Slot:** 50 min total · 32 min content · 13 min demo · 5 min Q&A

## Part 0 — Framing (4 min)

- "AI feature" → "AI-native": most talks stop at the model and the prompt.
- The two things that decide whether an agentic system is trustworthy at scale are invisible in demos: **what data reaches the agent**, and **what the agent is allowed to do**.
- Thesis slide: governance is not a wrapper around agents. It is a property of the data layer and the tool layer. Today we engineer both.

## Part 1 — FEED: the real-time data layer (10 min)

Engineering anchor. Vendor-neutral.

- Why agents quietly fail on stale data: confidently wrong, won't show in eval, shows in production.
- Batch / RAG-only is insufficient for agents that *act*.
- Three properties the data layer must give an agent:
  - **Freshness** — event time, not batch.
  - **Consistency** — idempotent writes, no double-action.
  - **Lineage** — every fact the agent saw is traceable. **← Bridge to Part 2: lineage is already an auditability primitive.**
- One abstracted field story (timeout / offset / consistency).

## Part 2 — FENCE: the agent–tool boundary as a governance surface (10 min) *— heart of the talk*

- LLM that talks → prompt safety. Agent that acts → **tool governance.** Different problem.
- MCP reframed: not "a way to give Claude tools" but **a typed, auditable, access-controlled contract for what an agent may touch.**
- **The model is untrusted; the server is the trust boundary.** That inverts where you put your engineering effort.
- Map governance concepts → concrete MCP mechanisms (this slide → demo beats):

| Governance concept    | MCP mechanism                                       | Lives in repo                            | Demo beat |
|-----------------------|-----------------------------------------------------|------------------------------------------|-----------|
| Use-case tiering      | Tools partitioned by tier in policy.yaml            | `policy.yaml`, `server/identity.py`      | Beat 2    |
| Identity & access     | Server enforces, not the model                      | `server/identity.py`                     | Beat 2    |
| Shadow mode           | Write tools simulate + log instead of executing     | `server/shadow.py`                       | Beat 3    |
| Human oversight       | Approval-gated tools suspend until human confirms   | `server/approvals.py` + `scripts/approve.py` | Beat 4 |
| Auditability          | Every call → structured event on a Kafka topic      | `server/audit.py` + `scripts/audit_viewer.py` | Beat 5 |

## Part 3 — SCALE: what breaks (8 min)

- **Multi-model routing** by cost/risk with logged routing decisions. → Beat 6 makes this concrete.
- Tool-call latency, tracing agent→tool→data, timeout/retry, idempotency under retries.
- Encoding operational expertise as reusable agent capability (Skills/subagents).
- Close: **governance is engineering — it lives in the data layer and the tool layer, not in a policy deck.**

## Demo (13 min) — six beats

See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). Each beat re-runs a Part 2/3 slide.

## Q&A (5 min)

Likely questions to be ready for:

- *Why MCP and not just function-calling?* MCP makes the boundary a process with its own auth, observability, and lifecycle — function-calling collapses it into the LLM call.
- *Doesn't shadow mode mean the agent learns to expect success?* Yes — that's exactly why you keep shadow + execute structurally identical and analyze the would-be effects separately.
- *Cost of multi-model routing?* Budgeted per tier. See "Production hardening" in README.
- *Why Kafka vs. just a database?* Lineage is the through-line. The audit log IS a stream, by design — same primitive as the data layer.
- *What about prompt injection?* Out of scope for this talk. Prompt injection threatens what the agent *says*; the server fences what the agent *does*. Both matter, but they're different talks.
