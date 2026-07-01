# TRACELOG vs. Langfuse

TRACELOG and Langfuse solve adjacent but distinct problems. This document outlines the architectural differences and helps teams decide which tool — or combination of tools — fits their use case.

## At a Glance

| | **Langfuse** | **TRACELOG** |
|---|---|---|
| Core focus | LLM observability | Log-to-action automation |
| Primary output | Traces, metrics, dashboards | Compressed incident summaries + proposed fixes |
| Data handling | Stores raw traces/prompts/outputs (Postgres/ClickHouse) | Distills logs locally before storage |
| Model dependency | Typically cloud-LLM oriented | Runs fully on local models (Ollama/Qwen/Gemma) |
| Interface | Web dashboard for engineers | Slack-based human-in-the-loop workflow |
| Deployment footprint | Mature, built for enterprise scale | Modular, six lightweight services |

In short: **Langfuse tells you what happened. TRACELOG proposes what to do next — and, with approval, can act on it.**

## When TRACELOG Is the Better Fit

### 1. You need remediation, not just visibility
Langfuse is an observability layer: it visualizes latency, errors, and traces, but a human still has to act on that information. TRACELOG's M5 Sandbox module can isolate an error, test a candidate fix in a sandboxed environment, and route it through the M6 Slack module for human approval. This shifts the workflow from "monitor and report" to "detect, propose, and act with a human in the loop."

### 2. Log volume and storage cost are a concern
High-traffic systems that log raw traces, prompts, and outputs can accumulate database bloat and, when paired with cloud LLMs, significant cost. TRACELOG's M3 Compression module uses rule-based detection with an optional LLM fallback to semantically distill logs before they're stored — collapsing repetitive, noisy traces into a compact incident summary. This also helps keep an agent's context window from being flooded with redundant data.

### 3. Fully local or air-gapped deployment is a requirement
TRACELOG is designed to run entirely on local models via Ollama (Qwen, Gemma, etc.), with no external network dependency. This is relevant for regulated environments — finance, defense, healthcare, or jurisdictions with strict data-residency requirements — where sending logs or code to a third-party cloud isn't an option. Langfuse also supports self-hosting; the distinction is that TRACELOG's architecture is local-first by default. Whether Langfuse's self-hosted mode meets a specific air-gapped requirement depends on the deployment and should be verified against its current documentation.

### 4. Non-technical stakeholders need to be in the loop
Langfuse's dashboard is built for engineers. TRACELOG's M6 Slack Bot brings status and approvals into the channels teams already use, via slash commands (`/tracelog status`, `/tracelog logs`, `/tracelog alerts`, etc.), making it easier for non-technical stakeholders to follow and approve agent actions without learning a new interface.

## When Langfuse Is the Better Fit

- **Deep, long-term analytics** — Langfuse offers a mature feature set for prompt versioning, A/B testing, and detailed cost/latency analytics that TRACELOG doesn't aim to replicate.
- **Large-scale, multi-tenant observability** — Langfuse's ecosystem and tooling are more established for this.
- **Existing cloud-LLM, Langfuse-based stacks** — if a team is already integrated with Langfuse and cloud models, the migration cost may outweigh the benefit.
- **Monitoring without automated remediation** — if visibility alone is sufficient, Langfuse's observability-only scope introduces less operational complexity.

## Decision Guide

| Need | Recommended tool |
|---|---|
| Visibility into what happened | Langfuse |
| Detection + proposed fix + human approval | TRACELOG |
| Log storage cost or context-window bloat | TRACELOG (M3 Compression) |
| Air-gapped / zero external data sharing | TRACELOG |
| Operations managed through Slack | TRACELOG (M6) |
| Comprehensive dashboards and analytics | Langfuse |

The two tools are not mutually exclusive. Some teams run Langfuse for high-level observability while using TRACELOG as the compression and autonomous-remediation layer underneath it.
