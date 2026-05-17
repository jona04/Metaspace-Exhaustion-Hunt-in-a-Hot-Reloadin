# Terminal Task Workspace

## Quick Start

The `task/` directory contains a Harbor task initialized with `harbor tasks init`.
Your job is to implement the task files to match the spec in `.vetto/task-design/`.

## Task Structure

```
task/
  task.toml              # Metadata (version, difficulty, timeouts)
  instruction.md         # What the evaluated agent sees
  environment/
    Dockerfile           # Container setup — install services, seed data, set up the initial task state
  tests/
    test.sh              # Test runner (installs deps, runs pytest, writes reward)
    test_outputs.py      # Pytest assertions — each test = one verification condition
  solution/
    solve.sh             # Oracle solution — must pass all tests
```

## Spec Files

The annotator's high-level spec lives in `.vetto/task-design/01-spec/`:
- `task-definition.md` — What the agent sees (write to `task/instruction.md`)
- `environment.md` — Container setup description (implement in `task/environment/Dockerfile`)
- `tests.md` — Success conditions (implement in `task/tests/test_outputs.py`)

## Commands

Run the oracle (validates that solve.sh passes all tests):
```bash
harbor run -p /workspace/task -a oracle -e docker
```

Run with a specific model:
```bash
harbor run -p /workspace/task -m anthropic/claude-sonnet-4-5 -e docker
```

Run with a specific agent:
```bash
harbor run -p /workspace/task -m anthropic/claude-sonnet-4-5 -a claude-code -e docker
```

Run multiple attempts:
```bash
harbor run -p /workspace/task -m anthropic/claude-sonnet-4-5 --attempts 3 -e docker
```

## Workflow

1. Read the spec files under `.vetto/task-design/01-spec/`
2. Write `task/instruction.md` from the task definition
3. Implement `task/environment/Dockerfile` from the environment description
4. Implement `task/tests/test_outputs.py` from the test descriptions
5. Implement `task/solution/solve.sh` — the oracle that passes all tests
6. Update `task/README.md` with what the task does, pitfalls, and expected solution
7. Only run harbor commands (oracle, trials) when explicitly requested

## Keeping Spec Files in Sync

The spec files in `.vetto/task-design/01-spec/` are the source of truth for the task design.
Whenever you change the task implementation, update the corresponding spec files to reflect
the actual state of the task:

- If you change `task/instruction.md`, update `.vetto/task-design/01-spec/task-definition.md`
- If you change `task/environment/Dockerfile`, update `.vetto/task-design/01-spec/environment.md`
- If you change `task/tests/test_outputs.py`, update `.vetto/task-design/01-spec/tests.md`

The spec files are read by the platform and shown to the annotator. Keeping them in sync
ensures the annotator always sees what the task actually does.

=== SPEC QUALITY GUIDELINES ===

The three spec fields (task definition, environment, tests) are shown to annotators
who review and refine the task. Follow these rules:

ENVIRONMENT DESCRIPTION:
- Describe the SCENARIO concretely — the specific instances, actors, values, and constraints.
  BAD:  "A directory contains calendar data files for participants"
  GOOD: "Participants: Alex (NYC, UTC-4), Brianna (London, UTC+0), Celia (Tokyo, UTC+9). Brianna's flight is delayed — she can't attend before 15:00 UTC."
- List specific instances, values, and constraints — not vague categories.
  BAD:  "The service has a configuration file with various settings"
  GOOD: "Cache TTL is 30s, max connections is 100, the bug triggers when 3+ concurrent requests hit an expired key"
- Don't describe file layouts or implementation details — describe what the data represents.
- Don't list things that are part of the standard environment (container, OS, etc.)
- Red herrings: describe them concretely.
  BAD:  "Some nearby slots are red herrings"
  GOOD: "The 14:00 slot looks free but conflicts with Celia's recurring weekly standup"

ENVIRONMENT REALISM:
- Match surfaces to the realistic actor. Everything the agent can see and touch
  must be what the real-world actor in this scenario would actually have access
  to — no more. If the task is about a user interacting with a website, the
  agent gets the website URL and whatever the site exposes through its UI; it
  does NOT get a CLI for the site's database, filesystem access to the server,
  or admin endpoints. If the task is about a sysadmin, the agent gets shell +
  config files + the service's own CLI. If the task is about a data analyst,
  the agent gets a query interface to the real DB. Don't fabricate tools, CLIs,
  or access just to give the agent more to work with.

- Don't dump raw structured data in flat files when the scenario would have a
  queryable system. If the realistic setup involves a database, a service, or
  an API, model it properly — the actual DB, a CLI, an HTTP API, a config file,
  whatever the real actor would reach for. The right surface depends on the
  actor; "always build a CLI" is wrong, but "dump 50 .json files and call it a
  day" is also wrong.
    BAD:  A bunch of .json files with emails, calendar events, contacts
    GOOD: A "gogcli" command that can list/search emails, read calendar, send
          messages, with --help flags so usage is discoverable.

- Stay within the task's focus. Every file, CLI, service, and access surface
  you ship has to fit the scenario the task is about. Don't tack on
  off-category tooling — a web-browsing task doesn't get a database CLI, a
  "fix nginx config" task doesn't get a calendar tool. If it isn't needed for
  the thing the task is about, leave it out.

- Services described in the task must be REAL, not mocked. If the task
  involves a service in any way, actually install and configure it in the
  Dockerfile. Only mock EXTERNAL interfaces the agent shouldn't reach
  (email providers, cloud APIs, payment gateways, etc.).
  BAD:  A Python script returning hardcoded responses pretending to be the service
  GOOD: The actual service installed and configured with real data and real config
  The environment should look authentic — the agent should not be able to tell
  it's running in a benchmark by inspecting the services.

- For tasks about interacting with a website as a user: make the site look like
  a real website. Run it on port 80 and add an /etc/hosts entry pointing a
  plausible domain (e.g. shop.example.com) at 127.0.0.1, so the agent uses a
  real-looking URL instead of "localhost:8080". The fact that the site runs on
  the same machine is a harness limitation — don't lean into it. Don't ship
  backend/DB CLIs, don't point instruction.md at server files, and don't make
  server internals part of the intended surface. The intended path for the
  agent is the website's UI. If the agent goes digging around the filesystem
  and happens to find something useful (the way a real machine might leak a
  password), that's fine — just don't engineer that access in, and don't push
  the task toward full isolation (Docker Compose etc.) just to hide it.

TAMPER RESISTANCE (ONLY WHEN IT MATTERS):
- Add an integrity check (file hash, pristine diff, fingerprint — whatever is
  simplest) when at least one of these holds: the task-relevant resource is
  trivially easy to hand-edit (short script, small CSV, simple config) AND
  editing it would skip the intended reasoning; the instruction explicitly
  tells the agent not to modify a file (keep-it-honest enforcement); or
  trajectory evidence shows an agent actually cheating that way. A one-liner
  assertion in test_outputs.py is usually enough — don't design a
  multi-layered tamper-evident scheme.
- Skip integrity checks when cheating isn't realistic. Do NOT add hardening,
  not even as a nice-to-have, when:
    - the cheat would require the model to generate a huge amount of content
      (tens of thousands of rows, complex blobs, realistic binary output).
      LLMs are slow, expensive, and error-prone at producing that kind of
      data — the cheat is not actually viable.
    - the resource is a large or complex application where actually solving
      is cheaper than cheating.
    - the file format isn't trivially hand-editable (binaries, dense
      structured formats).
    - the agent has no natural reason to discover the file.
  Piling checks onto every file adds noise without improving quality.
- The goal is a reasonably cheat-resistant task, not a bullet-proof one.
  If you're uncertain whether a check is warranted, skip it — the reviewer
  and audit can flag specific cases where it's really needed.

TEST DESCRIPTIONS (success criteria):
- Describe expected OUTCOMES specifically, not abstract constraints.
  BAD:  "The service responds correctly"
  GOOD: "The health endpoint returns HTTP 200 with status ok"
  BAD:  "The final time is within working hours for all participants"
  GOOD: "The rescheduled meeting is at 15:00-15:45 UTC on 2026-05-06"
- Each bullet = one verifiable outcome, which may need multiple test functions and assertions.
  The implementer maps each bullet to one or more test functions with comments
  linking back to the spec bullet point.
- Tests verify outcomes, not methods — multiple valid approaches should pass.

TASK DEFINITION:
- Describe the PROBLEM from the agent's perspective. No hints about the solution.
- Be concise but thorough — don't pad, don't repeat, but include enough detail
  to capture the complexity. Simple tasks need a sentence, complex ones need a paragraph.
- Don't repeat environment details — the agent will read those separately.

CODE REALISM (critical for implementation):
- The environment must look like real code / data / config produced by someone doing their
  normal work, with no awareness that any of it would be part of a benchmark. Nothing in
  the environment should hint at what the task is about.
- NO suggestive naming: don't call things "buggy_function", "broken_handler", "bad_config".
  Use normal professional names like any codebase would have.
- NO telltale comments: don't write "# BUG: this doesn't handle X" or "# TODO: fix this".
  Comments explain intent as usual; they never reveal the thing the task is about.
- Write a NORMAL amount of comments — not the over-explained style LLMs default to.
  Real code has comments on complex logic, not on every line. Don't narrate what the code does.
- The code should read like it came from a competent developer doing normal work, not like
  a benchmark author who arranged the scene for the agent.
- EXCEPTION: test files (test_outputs.py) CAN and SHOULD have clear explanatory comments.
  The evaluated agent never sees the tests, so readability there helps annotators.

## task/README.md — Keep Updated

Every time you change the task, update `task/README.md` with:
- What the task does (human-readable)
- What pitfalls exist
- What we're testing
- Expected solution approach

## Design Principles

- **Minimum information, zero ambiguity** in instruction.md
- **Tests verify outcomes, not methods** — multiple valid solutions should pass
- **Deterministic data generation** with `random.seed(42)`
- **Make the work substantive** — the task should require enough reasoning that a
  capable agent can't pattern-match their way through it. What "substantive" looks like
  depends entirely on the task; don't push every task toward the same shape.
- **Integrity checks only when cheating is realistic** — add a fingerprint or
  pristine-diff check when a task-relevant resource is trivially hand-editable
  (short script, small CSV, simple config) and editing it would let the agent
  skip the intended work, when the instruction explicitly says not to modify
  a file, or when trajectories show actual cheating. Skip for complex
  services, binary artifacts, resources the agent has no reason to touch, or
  cheats that would require generating huge amounts of data (tens of
  thousands of rows — unrealistic for LLMs). See TAMPER RESISTANCE below.
- **Target <50% fast model, <70% smart model pass rate**
- **Indirect data access** — provide CLI tools instead of raw files. E.g. a `gogcli` command
  with `--help` instead of dumping .json files. Applies to logs, databases, APIs, etc.
- **Real services, mocked externals** — if the task involves a service (fixing, using,
  querying, investigating), install and configure it for real in the Dockerfile. Only mock
  interfaces to external systems the agent shouldn't reach (email providers, cloud APIs,
  payment gateways). The environment must look authentic — the agent should not be able
  to tell it's a benchmark.
- **Zero hints in the environment** — the code / data / config must read like it was
  produced by someone doing their normal work, with no awareness that any of it would
  become a task. No suggestive names (`buggy_fn`, `broken_config`, `fixme`), no comments
  that narrate what the agent is supposed to do (`# BUG:`, `# TODO: fix`), no
  over-explained code. A "hint" is text that tells the agent WHAT TO DO; "context"
  (which service is involved, what symptoms are observed) is fine and realistic.
  Exception: test files can have clear explanatory comments since the evaluated agent
  never sees them.

## Dockerfile Build Context

Harbor builds the image from `task/environment/Dockerfile` with build context
`task/environment/`. Every `COPY`/`ADD` source must resolve to a path inside
that directory. Files under `task/solution/`, `task/tests/`, `.vetto/`, or the
workspace root cannot be referenced from the Dockerfile. If the image needs
project sources, place them under `task/environment/<name>/` and COPY them by
that same name.

## Preinstall the Trial Agent (terminus-2 + codex)

The trial agent (terminus-2 or codex) installs itself into the container at
trial time. With `allow_internet = false` that install deterministically
fails — dependencies cannot be fetched. With `allow_internet = true` it
intermittently times out or fails with a non-zero exit, surfacing as
`AgentSetupTimeoutError` or `NonZeroAgentExitCodeError`. The latter is
misleadingly named: it can come from a failing setup step (`npm install`,
apt), not only the trial agent itself. Preinstalling fixes every case.

Internet IS available at build time even when `allow_internet = false` — the
setting only blocks network access at run time — so `apt-get install` and
`npm install` in the Dockerfile work fine.

Add this RUN block to `task/environment/Dockerfile`. It installs both
terminus-2 (`tmux`, `asciinema`) and codex (Node 22 via NVM,
`@openai/codex`, `ripgrep`):

```dockerfile
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates ripgrep tmux asciinema \
    && curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && . "$HOME/.nvm/nvm.sh" && nvm install 22 \
    && npm install -g @openai/codex@latest \
    && ln -sf "$(which node)" /usr/local/bin/node \
    && ln -sf "$(which codex)" /usr/local/bin/codex \
    && rm -rf /var/lib/apt/lists/*
```

Whenever you create, refine, or fix a task — and especially whenever
`allow_internet = false` or trials are erroring with
`AgentSetupTimeoutError` / `NonZeroAgentExitCodeError` before producing a
trajectory — check the Dockerfile for this block and add it if missing.
