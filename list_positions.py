#!/usr/bin/env python3
"""List positions from a running IB Gateway/TWS session."""

import argparse
import sys
from typing import List

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
            ib.connect(args.host, port, clientId=args.client_id, timeout=4)
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

    print("account,secType,symbol,localSymbol,qty,avgCost")
    for pos in positions:
        c = pos.contract
        print(
            f"{pos.account},{c.secType},{c.symbol},{getattr(c, 'localSymbol', '')},"
            f"{pos.position},{pos.avgCost}"
        )

    ib.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
