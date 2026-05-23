#!/usr/bin/env python3
"""List positions from a running IB Gateway/TWS session."""

import argparse
import sys
from typing import Dict, List, Tuple

from ib_insync import IB


def parse_ports(value: str) -> List[int]:
    ports = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        ports.append(int(item))
    if not ports:
        raise ValueError("No ports provided")
    return ports


def contract_key(account: str, contract) -> Tuple[str, int, str, str, str]:
    return (
        account,
        getattr(contract, "conId", 0),
        getattr(contract, "secType", ""),
        getattr(contract, "symbol", ""),
        getattr(contract, "localSymbol", ""),
    )


def fmt_money(value: float) -> str:
    return f"{value:.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def print_table(headers: List[str], rows: List[List[str]]) -> None:
    widths = [
        max(len(str(row[index])) for row in [headers] + rows)
        for index in range(len(headers))
    ]
    numeric_headers = {"Qty", "Avg Cost", "Market Value", "Portfolio %"}

    def format_row(row: List[str]) -> str:
        cells = []
        for index, value in enumerate(row):
            text = str(value)
            if headers[index] in numeric_headers:
                cells.append(text.rjust(widths[index]))
            else:
                cells.append(text.ljust(widths[index]))
        return "  ".join(cells)

    print(format_row(headers))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))


def main() -> int:
    parser = argparse.ArgumentParser(description="List IBKR account positions.")
    parser.add_argument("--host", default="127.0.0.1", help="IB Gateway/TWS host")
    parser.add_argument(
        "--ports",
        default="4002,4001,4000,7497,7496",
        help="Comma-separated ports to try in order",
    )
    parser.add_argument("--client-id", type=int, default=201, help="IB API clientId")
    parser.add_argument(
        "--timeout",
        type=float,
        default=15,
        help="IB API connection timeout in seconds",
    )
    parser.add_argument(
        "--account",
        default="",
        help="Optional account filter (e.g. DU1234567)",
    )
    args = parser.parse_args()

    try:
        ports = parse_ports(args.ports)
    except Exception as exc:
        print(f"Invalid --ports value: {exc}")
        return 2

    ib = IB()
    connected_port = None
    for port in ports:
        try:
            ib.connect(
                args.host,
                port,
                clientId=args.client_id,
                timeout=args.timeout,
                readonly=True,
            )
            if ib.isConnected():
                connected_port = port
                break
        except Exception:
            continue

    if connected_port is None:
        print(f"ERROR: could not connect to {args.host} on ports {ports}")
        return 3

    accounts = ib.managedAccounts()
    print(f"Connected: {args.host}:{connected_port}")
    print(f"Managed accounts: {accounts}")

    positions = ib.positions()
    if args.account:
        positions = [p for p in positions if p.account == args.account]

    if not positions:
        print("No positions.")
        ib.disconnect()
        return 0

    portfolio_items = ib.portfolio()
    if args.account:
        portfolio_items = [p for p in portfolio_items if p.account == args.account]
    portfolio_by_key: Dict[Tuple[str, int, str, str, str], float] = {
        contract_key(item.account, item.contract): float(item.marketValue or 0)
        for item in portfolio_items
    }

    rows = []
    for pos in positions:
        c = pos.contract
        market_value = portfolio_by_key.get(contract_key(pos.account, c))
        if market_value is None:
            if c.secType == "CASH":
                market_value = float(pos.position or 0)
            else:
                market_value = float(pos.position or 0) * float(pos.avgCost or 0)
        rows.append((pos, market_value))

    total_market_value = sum(
        market_value for pos, market_value in rows if pos.contract.secType != "CASH"
    )

    table_rows = []
    for pos, market_value in rows:
        c = pos.contract
        portfolio_pct = (
            market_value / total_market_value * 100
            if c.secType != "CASH" and total_market_value
            else 0
        )
        table_rows.append(
            [
                pos.account,
                c.secType,
                c.symbol,
                getattr(c, "localSymbol", ""),
                str(pos.position),
                str(pos.avgCost),
                fmt_money(market_value),
                fmt_pct(portfolio_pct),
            ]
        )
    print_table(
        [
            "Account",
            "Sec Type",
            "Symbol",
            "Local Symbol",
            "Qty",
            "Avg Cost",
            "Market Value",
            "Portfolio %",
        ],
        table_rows,
    )

    ib.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
