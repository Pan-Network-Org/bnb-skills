#!/usr/bin/env python3
"""
Transfer BNB on BNB Chain (BSC).

Usage:
    python3 transfer_bnb.py \
        --private-key 0xYOURKEY \
        --to 0xRECIPIENT \
        --amount 0.01 \
        [--rpc https://bsc-dataseed.binance.org] \
        [--gas-price 3] \
        [--dry-run]

Options:
    --private-key   Sender's private key (hex, with or without 0x prefix)
    --to            Recipient address
    --amount        Amount in BNB to send
    --rpc           BSC RPC endpoint (default: public Binance RPC)
    --gas-price     Gas price in Gwei (default: 3)
    --dry-run       Simulate without broadcasting
"""

import argparse
import sys
from decimal import Decimal
from web3 import Web3


BSC_RPC_URLS = [
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed1.defibit.io/",
    "https://bsc-dataseed1.ninicoin.io/",
    "https://rpc.ankr.com/bsc",
]


def connect(rpc_url=None):
    urls = [rpc_url] if rpc_url else BSC_RPC_URLS
    for url in urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                print(f"[✓] Connected to RPC: {url} (chain_id={chain_id})")
                return w3
        except Exception:
            continue
    print("Error: Cannot connect to any BSC RPC endpoint.", file=sys.stderr)
    sys.exit(1)


def transfer_bnb(private_key, to_address, amount_bnb, rpc_url=None, gas_price_gwei=3, dry_run=False):
    w3 = connect(rpc_url)

    # Normalize private key
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    account = w3.eth.account.from_key(private_key)
    sender = account.address

    # Validate recipient
    if not Web3.is_address(to_address):
        print(f"Error: Invalid recipient address: {to_address}", file=sys.stderr)
        sys.exit(1)
    to_checksum = Web3.to_checksum_address(to_address)

    # Check balance
    balance_wei = w3.eth.get_balance(sender)
    balance_bnb = w3.from_wei(balance_wei, "ether")
    amount_wei = w3.to_wei(Decimal(str(amount_bnb)), "ether")

    gas_limit = 21000
    gas_price_wei = w3.to_wei(gas_price_gwei, "gwei")
    fee_wei = gas_limit * gas_price_wei
    total_needed = amount_wei + fee_wei

    print(f"\n{'='*60}")
    print(f"  BNB Transfer Summary")
    print(f"{'='*60}")
    print(f"  From        : {sender}")
    print(f"  To          : {to_checksum}")
    print(f"  Amount      : {amount_bnb} BNB")
    print(f"  Gas Price   : {gas_price_gwei} Gwei")
    print(f"  Estimated Fee: {w3.from_wei(fee_wei, 'ether'):.6f} BNB")
    print(f"  Sender Balance: {float(balance_bnb):.6f} BNB")
    print(f"{'='*60}")

    if balance_wei < total_needed:
        print(f"\n❌ Insufficient balance!")
        print(f"   Need : {w3.from_wei(total_needed, 'ether')} BNB")
        print(f"   Have : {float(balance_bnb):.6f} BNB")
        sys.exit(1)

    if dry_run:
        print("\n[DRY RUN] Transaction NOT broadcast. All checks passed ✓")
        return None

    nonce = w3.eth.get_transaction_count(sender, "pending")
    tx = {
        "nonce": nonce,
        "to": to_checksum,
        "value": amount_wei,
        "gas": gas_limit,
        "gasPrice": gas_price_wei,
        "chainId": w3.eth.chain_id,
    }

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hex = tx_hash.hex()

    print(f"\n[✓] Transaction sent!")
    print(f"  TX Hash : {tx_hex}")
    print(f"  BSCScan : https://bscscan.com/tx/{tx_hex}")

    print("\n  Waiting for confirmation...", end="", flush=True)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    status = "✅ Success" if receipt["status"] == 1 else "❌ Failed"
    print(f"\n  Status  : {status}")
    print(f"  Block   : {receipt['blockNumber']}")
    print(f"  Gas Used: {receipt['gasUsed']}")
    print(f"{'='*60}\n")

    return tx_hex


def main():
    parser = argparse.ArgumentParser(description="Transfer BNB on BNB Chain")
    parser.add_argument("--private-key", required=True, help="Sender's private key")
    parser.add_argument("--to", required=True, dest="to_address", help="Recipient address")
    parser.add_argument("--amount", required=True, type=float, help="Amount in BNB")
    parser.add_argument("--rpc", default=None, help="Custom RPC URL")
    parser.add_argument("--gas-price", type=float, default=3.0, help="Gas price in Gwei (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without broadcasting")
    args = parser.parse_args()

    transfer_bnb(
        private_key=args.private_key,
        to_address=args.to_address,
        amount_bnb=args.amount,
        rpc_url=args.rpc,
        gas_price_gwei=args.gas_price,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
