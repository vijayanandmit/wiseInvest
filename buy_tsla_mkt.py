#!/usr/bin/env python3
"""Place a TSLA market BUY order in DU2540043 with qty input."""

import argparse
import sys
from typing import List

from ib_insync import IB, MarketOrder, Stock, StopOrder


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
        description="Buy TSLA with a market order in account DU2540043."
    )
    parser.add_argument("qty", type=float, help="Quantity to buy (must be > 0)")
    parser.add_argument("--host", default="127.0.0.1", help="IB Gateway/TWS host")
    parser.add_argument(
        "--ports",
        default="4002,4001,4000,7497,7496",
        help="Comma-separated ports to try in order",
    )
    parser.add_argument("--client-id", type=int, default=203, help="IB API clientId")
    parser.add_argument(
        "--stop-loss-pct",
        type=float,
        default=5.0,
        help="Place protective stop-loss SELL at this percent below entry (0 disables)",
    )
    parser.add_argument(
        "--stop-tif",
        default="GTC",
        help="Time in force for stop-loss order (e.g. DAY, GTC)",
    )
    args = parser.parse_args()

    if args.qty <= 0:
        print("ERROR: qty must be > 0")
        return 2
    if args.stop_loss_pct < 0:
        print("ERROR: --stop-loss-pct must be >= 0")
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

    contract = Stock("TSLA", "SMART", "USD")
    qualified = ib.qualifyContracts(contract)
    if not qualified:
        print("ERROR: could not qualify TSLA contract")
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
    print(f"Order: BUY {args.qty} TSLA MKT")
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

    # Place protective stop-loss only after entry fill so trigger is based on real fill price.
    if args.stop_loss_pct > 0:
        filled_qty = trade.orderStatus.filled or 0
        avg_fill = trade.orderStatus.avgFillPrice or 0

        if trade.fills:
            # Fallback to execution details if orderStatus has not fully refreshed yet.
            exec_qty = sum(f.execution.shares for f in trade.fills if f.execution)
            if exec_qty > filled_qty:
                filled_qty = exec_qty
            if avg_fill <= 0:
                avg_fill = trade.fills[-1].execution.price

        if filled_qty <= 0:
            print(
                "StopLoss: not placed because entry has no filled quantity yet. "
                "Re-run after fill or use bracket-style order flow."
            )
            ib.disconnect()
            return 0

        if avg_fill <= 0:
            print("StopLoss: not placed because entry fill price is unavailable.")
            ib.disconnect()
            return 0

        stop_price = round(avg_fill * (1 - args.stop_loss_pct / 100), 2)
        stop_order = StopOrder(
            "SELL",
            filled_qty,
            stop_price,
            account="DU2540043",
            tif=args.stop_tif,
        )
        stop_trade = ib.placeOrder(qc, stop_order)
        # Give IB a moment to acknowledge the stop order state.
        for _ in range(10):
            ib.sleep(0.5)
            if stop_trade.orderStatus.status:
                break
        print(
            f"StopLoss: SELL {filled_qty} {qc.symbol} "
            f"STP {stop_price} tif={args.stop_tif}"
        )
        print(
            f"StopOrderId: {stop_trade.order.orderId} "
            f"StopPermId: {stop_trade.order.permId}"
        )
        print(f"StopStatus: {stop_trade.orderStatus.status}")
        if stop_trade.log:
            last_stop_log = stop_trade.log[-1]
            print(
                f"StopLastLog: status={last_stop_log.status} "
                f"message={last_stop_log.message}"
            )

    ib.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
