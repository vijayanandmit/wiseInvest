#!/usr/bin/env python3
"""Place a buy order through a running IB Gateway/TWS session."""

import argparse
import sys
from typing import List

from ib_insync import IB, LimitOrder, MarketOrder, Stock


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
    parser = argparse.ArgumentParser(description="Place an IBKR BUY order.")
    parser.add_argument("--host", default="127.0.0.1", help="IB Gateway/TWS host")
    parser.add_argument(
        "--ports",
        default="4002,4001,4000,7497,7496",
        help="Comma-separated ports to try in order",
    )
    parser.add_argument("--client-id", type=int, default=202, help="IB API clientId")
    parser.add_argument("--account", default="", help="Optional account (e.g. DU1234567)")
    parser.add_argument("--symbol", default="GEV", help="Stock symbol to buy")
    parser.add_argument("--qty", type=float, default=1, help="Quantity to buy")
    parser.add_argument(
        "--order-type",
        choices=["MKT", "LMT"],
        default="MKT",
        help="Order type",
    )
    parser.add_argument("--limit-price", type=float, default=0.0, help="Limit price for LMT")
    parser.add_argument("--tif", default="DAY", help="Time in force (e.g. DAY, GTC)")
    args = parser.parse_args()

    try:
        ports = parse_ports(args.ports)
    except Exception as exc:
        print(f"Invalid --ports value: {exc}")
        return 2

    if args.qty <= 0:
        print("ERROR: --qty must be > 0")
        return 2
    if args.order_type == "LMT" and args.limit_price <= 0:
        print("ERROR: --limit-price must be > 0 for LMT orders")
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
    account = args.account or (accounts[0] if accounts else "")
    if not account:
        print("ERROR: no managed account found; pass --account explicitly")
        ib.disconnect()
        return 4

    contract = Stock(args.symbol, "SMART", "USD")
    qualified = ib.qualifyContracts(contract)
    if not qualified:
        print(f"ERROR: could not qualify stock contract for {args.symbol}")
        ib.disconnect()
        return 5

    qc = qualified[0]
    if args.order_type == "MKT":
        order = MarketOrder("BUY", args.qty, account=account, tif=args.tif)
    else:
        order = LimitOrder("BUY", args.qty, args.limit_price, account=account, tif=args.tif)

    trade = ib.placeOrder(qc, order)
    terminal = {"Filled", "Cancelled", "Inactive", "ApiCancelled"}
    for _ in range(45):
        ib.sleep(1)
        if trade.orderStatus.status in terminal:
            break

    print(f"Connected: {args.host}:{connected_port}")
    print(f"Account: {account}")
    print(
        f"Order: BUY {args.qty} {qc.symbol} ({args.order_type}) status={trade.orderStatus.status}"
    )
    print(f"OrderId: {trade.order.orderId} PermId: {trade.order.permId}")
    print(
        f"Filled: {trade.orderStatus.filled} Remaining: {trade.orderStatus.remaining} "
        f"AvgFill: {trade.orderStatus.avgFillPrice}"
    )
    if trade.fills:
        last_fill = trade.fills[-1].execution
        print(
            f"LastFill: execId={last_fill.execId} shares={last_fill.shares} "
            f"price={last_fill.price} time={last_fill.time}"
        )
    if trade.log:
        last = trade.log[-1]
        print(f"LastLog: status={last.status} message={last.message}")

    ib.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
