Repository purpose

This repository holds small Interactive Brokers (IBKR) utilities and notes for setting up Codex/paper trading (see README.md and list_cli.md). The main runnable script is list_positions.py which connects to a running IB Gateway/TWS and prints account positions as CSV.

Build / test / lint commands

- No formal build, test, or lint tooling is configured in this repo.
- Python dependency: ib_insync. Install with:

  python3 -m pip install --user ib_insync

- To run the primary utility (single script):

  python3 list_positions.py

  With account filter:
  python3 list_positions.py --account DU1234567

  With custom host/ports:
  python3 list_positions.py --host 127.0.0.1 --ports 4002,4001,4000

High-level architecture

- Top-level utilities and notes only (no package or tests).
- list_positions.py: single-file CLI utility that:
  - cycles through a list of TCP ports to connect to IB Gateway/TWS via ib_insync.IB
  - queries managed accounts and positions
  - optionally filters positions by account and prints CSV rows
- README.md contains higher-level setup steps for Codex and paper trading.
- list_cli.md documents exact CLI examples and prerequisites (IB Gateway/TWS running, API socket enabled).

Key conventions and repo-specific patterns

- CLI behavior:
  - Uses argparse for options: --host, --ports (comma-separated), --client-id, --account
  - Default ports order: 4002,4001,4000,7497,7496
  - Default client-id: 201
  - Shebang present; scripts intended to be run with python3
- Exit codes used by list_positions.py:
  - 0: success (no positions or normal output)
  - 2: invalid --ports value
  - 3: could not connect to any provided ports
- Output format: CSV with header: account,secType,symbol,localSymbol,qty,avgCost
- External service dependency: requires a running IB Gateway/TWS session with API socket access enabled. Local runs will fail without Gateway/TWS.

Notes for Copilot sessions

- When editing or testing list_positions.py, remember it depends on a live IB connection. For unit-level modifications, mock ib_insync.IB or refactor to accept an IB instance to allow offline testing.
- No project-level test/lint config exists — if adding tests or linting, document commands here (pytest, tox, flake8, etc.).
- Check README.md and list_cli.md for operational examples and prerequisites before proposing CLI changes.

Other AI assistant configs

- No additional AI assistant configuration files were found (CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, CONVENTIONS.md, .clinerules, etc.).

Summary

Created .github/copilot-instructions.md capturing how to run the utilities, repo architecture, and conventions to guide future Copilot sessions. If any additional areas should be covered (tests, packaging, CI), say which and they will be added.