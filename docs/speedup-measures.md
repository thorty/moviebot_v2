# Performance Summary And Independent Implementation Steps

## Goal

This document captures the main reasons for the long runtime in the analyzed search trace and translates them into independent implementation steps.

Each step is intentionally designed so it can be implemented, tested, and rolled back on its own.

## Main Finding

The biggest performance issue is not one single external call. It is the combination of:

1. Multiple sequential LLM turns inside the research loop
2. Large tool outputs being fed back into the next LLM turn
3. Prompt instructions that explicitly encourage broad multi-search behavior

In the analyzed run, the research prompt size grew roughly like this:

- 2,973 input tokens
- 7,145 input tokens
- 9,474 input tokens
- 12,855 input tokens
- 31,831 input tokens

This means the strongest optimization lever is reducing context growth between tool calls and the next model invocation.

## Priority Order

Recommended implementation order:

1. Reduce tool payload size after filtering
2. Reduce tool payload size from Tavily
3. Reduce search breadth in the prompt
4. Add stricter early-stop behavior
5. Stop replaying full current-turn tool payload into the next LLM call
6. Split orchestration model from final response model
7. Add caching and better timing instrumentation

## Step 1: Remove Or Shrink raw_results From filter_streaming_providers

### Why

The filter tool currently returns both `available_titles` and `raw_results`. In the analyzed run, these contain almost the same result set, which inflates the next LLM call.

### Expected Impact

- High
- Estimated end-to-end improvement: 15 to 30 percent
- Estimated reduction of the final large LLM prompt: 30 to 60 percent

### Scope

Change only the filter tool return payload.

### Likely Files

- backend/tools.py

### Implementation Options

Option A:
- Remove `raw_results` completely from the tool response

Option B:
- Keep `raw_results` only behind a debug flag

Option C:
- Replace `raw_results` with a compact summary only

### Independent Test

Run the same query again and verify:

- Functional output still looks correct
- `found_count` remains unchanged
- Final LLM input tokens drop noticeably

### Risk

- Low
- Only risky if downstream logic relies on `raw_results` implicitly

## Step 2: Return Compact Tavily Results Instead Of Full Snippets

### Why

The Tavily tool returns long content snippets. Those snippets are useful for manual inspection but are often too large for repeated agent loops.

### Expected Impact

- Medium to high
- Estimated end-to-end improvement: 10 to 20 percent
- Bigger gain if multiple Tavily searches are still allowed

### Scope

Change only the Tavily tool output format.

### Likely Files

- backend/tools.py

### Suggested Compact Shape

For each result, keep only:

- title
- url
- short snippet with hard cap, for example 200 to 300 characters
- score

Drop:

- long `content`
- unused fields
- optional raw payloads

### Independent Test

Run a search and verify:

- The model still extracts enough titles
- Tavily tool messages become much smaller
- No loss in recommendation quality for simple queries

### Risk

- Low to medium
- If made too aggressive, the model may miss niche titles

## Step 3: Reduce Search Breadth In The Research Prompt

### Why

The current prompt explicitly asks for:

- 3 to 5 strategic web queries
- 50 to 80 collected titles before filtering

That is too expensive for simple requests.

### Expected Impact

- Medium to high
- Estimated end-to-end improvement: 15 to 30 percent

### Scope

Prompt-only change.

### Likely Files

- backend/prompts.py

### Suggested Changes

Replace broad instructions with:

- 1 to 2 search queries for normal requests
- 10 to 20 candidate titles before filtering
- Escalate to broader search only when the first filter result is weak

### Independent Test

Compare before and after on the same query:

- Number of Tavily calls
- Number of candidates sent to filter tool
- Final quality of recommendations

### Risk

- Low
- Slight risk of fewer niche discoveries

## Step 4: Strengthen Early Stop Rules

### Why

The logic already contains an early-stop intent, but the system still performs several search loops before the filter pass. Early stopping should happen sooner and more deterministically.

### Expected Impact

- Medium
- Estimated end-to-end improvement: 10 to 20 percent

### Scope

Prompt and small graph behavior adjustment.

### Likely Files

- backend/prompts.py
- backend/graph.py

### Suggested Behavior

After the first successful filter result:

- If at least 4 strong candidates exist, stop immediately
- If at least 2 acceptable candidates exist, optionally stop for simple queries
- Do not perform new web searches once enough valid results already exist

### Independent Test

Verify on an easy query that:

- The flow stops after one search plus one filter round
- No unnecessary second research turn occurs

### Risk

- Low to medium
- Requires care to avoid cutting off difficult cases too early

## Step 5: Replace Full Tool Message Replay With Compact State Summary

### Why

This is likely the highest-impact structural optimization. Right now, the current turn's tool outputs remain available to the next research-model invocation. That makes prompt size grow step by step.

### Expected Impact

- Very high
- Estimated end-to-end improvement: 25 to 45 percent
- Estimated improvement on large-query traces: potentially more

### Scope

Graph-level change.

### Likely Files

- backend/graph.py
- backend/states.py

### Suggested Approach

Instead of replaying the full current-turn tool messages, write a compact summary into state, for example:

- Tavily search count
- extracted title count
- top candidate titles
- filter result count
- compact final candidate list with minimal metadata

Then pass only that compact summary into the next research-model call.

### Independent Test

Use the same trace scenario and verify:

- Final prompt tokens drop sharply
- Recommendations remain stable
- Tool loops still function correctly

### Risk

- Medium to high
- This is the first step that changes graph behavior more deeply

## Step 6: Use A Faster Model For Tool Orchestration

### Why

The current research model is strong but relatively expensive for repeated planning and tool selection turns.

### Expected Impact

- Medium
- Estimated end-to-end improvement: 10 to 25 percent

### Scope

Model configuration change.

### Likely Files

- backend/graph.py

### Suggested Split

- Faster model for research orchestration and tool choice
- Stronger model only for final phrasing if needed

### Independent Test

Compare:

- Same query quality
- Same tool usage correctness
- Lower wall-clock time per model turn

### Risk

- Medium
- Some models may be worse at reliable tool use

## Step 7: Add Response Caching And Better Timing Logs

### Why

The current trace is good for qualitative analysis but weak for exact latency attribution. Better measurement is needed to validate each optimization.

### Expected Impact

- Low direct speed gain from logging alone
- Medium long-term optimization value
- Caching itself can be high impact for repeated popular titles

### Scope

Infrastructure and observability.

### Likely Files

- backend/graph.py
- backend/tools.py
- backend/utils/tmdb/tmdb_api_client.py
- main.py

### Suggested Measurements

Log wall-clock duration for:

- each model invoke
- each Tavily search
- each filter tool execution
- TMDB batch resolution

### Suggested Caching Targets

- TMDB title resolution
- TMDB provider lookup
- repeated popular Tavily searches if acceptable

### Independent Test

Verify:

- logs show per-step timing clearly
- repeated identical requests benefit from cache hits

### Risk

- Low for timing logs
- Medium for caching if data freshness matters

## Suggested Testing Strategy

Test each step independently using the same fixed input query and compare:

1. Total runtime
2. Number of Tavily calls
3. Number of model invocations
4. Final model input tokens
5. Recommendation quality
6. Correctness of provider filtering

## Recommended First Change

If only one change should be implemented first, start with:

Step 1: Remove or shrink `raw_results`

Why this first:

- Minimal code change
- Low risk
- Easy to validate
- Directly attacks one of the clearest sources of prompt bloat

## Recommended Highest-Impact Change

If the goal is maximum latency reduction, the biggest single structural improvement is:

Step 5: Replace full tool message replay with compact state summary

Why this is highest impact:

- It attacks the core context growth problem
- It scales better across all query types
- It reduces repeated large-model work, not only one tool payload