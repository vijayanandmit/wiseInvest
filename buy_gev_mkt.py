#!/usr/bin/env python3
"""Place a GEV market BUY order in DU2540043 with qty input."""

import argparse
import sys
from typing import List

from ib_insync import IB, MarketOrder, Stock


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
    parser = argparse.ArgumentParser(
        description="Buy GEV with a market order in account DU2540043."
    )
    parser.add_argument("qty", type=float, help="Quantity to buy (must be > 0)")
    parser.add_argument("--host", default="127.0.0.1", help="IB Gateway/TWS host")
    parser.add_argument(
        "--ports",
        default="4002,4001,4000,7497,7496",
        help="Comma-separated ports to try in order",
    )
    parser.add_argument("--client-id", type=int, default=203, help="IB API clientId")
    args = parser.parse_args()

    if args.qty <= 0:
        print("ERROR: qty must be > 0")
        return 2

    try:
        ports = parse_ports(args.ports)
    except Exception as exc:
        print(f"ERROR: invalid --ports value: {exc}")
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

    contract = Stock("GEV", "SMART", "USD")
    qualified = ib.qualifyContracts(contract)
    if not qualified:
        print("ERROR: could not qualify GEV contract")
        ib.disconnect()
        return 4
    qc = qualified[0]

    order = MarketOrder("BUY", args.qty, account="DU2540043", tif="DAY")
    trade = ib.placeOrder(qc, order)

    terminal = {"Filled", "Cancelled", "Inactive", "ApiCancelled"}
    for _ in range(45):
        ib.sleep(1)
        if trade.orderStatus.status in terminal:
            break

    print(f"Connected: {args.host}:{connected_port}")
    print("Account: DU2540043")
    print(f"Order: BUY {args.qty} GEV MKT")
    print(f"Status: {trade.orderStatus.status}")
    print(f"OrderId: {trade.order.orderId} PermId: {trade.order.permId}")
    print(
        f"Filled: {trade.orderStatus.filled} Remaining: {trade.orderStatus.remaining} "
        f"AvgFill: {trade.orderStatus.avgFillPrice}"
    )
    if trade.fills:
        fill = trade.fills[-1].execution
        print(
            f"LastFill: execId={fill.execId} shares={fill.shares} "
            f"price={fill.price} time={fill.time}"
        )
    if trade.log:
        last = trade.log[-1]
        print(f"LastLog: status={last.status} message={last.message}")

    ib.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
