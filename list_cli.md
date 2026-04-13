# IBKR Utilities

## Prerequisites

- IB Gateway or TWS is running and logged into your paper account.
- API socket access is enabled in Gateway/TWS settings.
- Python dependency installed:

```bash
python3 -m pip install --user ib_insync
```

## List Positions

Exact command to run next time:

```bash
python3 /data/560054484/gitclones/IBKR/list_positions.py
```

Optional account filter:

```bash
python3 /data/560054484/gitclones/IBKR/list_positions.py --account DU2540043
```

Optional custom host/ports:

```bash
python3 /data/560054484/gitclones/IBKR/list_positions.py --host 127.0.0.1 --ports 4002,4001,4000,7497,7496
```

## Place Buy Order (GEV)

Exact command to execute a market buy for GEV:

```bash
python3 /data/560054484/gitclones/IBKR/place_buy_order.py --symbol GEV --qty 1 --order-type MKT --account DU2540043
```

Optional limit buy example:

```bash
python3 /data/560054484/gitclones/IBKR/place_buy_order.py --symbol GEV --qty 1 --order-type LMT --limit-price 300 --account DU2540043
```
