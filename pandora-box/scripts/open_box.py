#!/usr/bin/env python3
"""
Open a PANdoraBox mystery box on BNB Chain.

Usage:
    python3 open_box.py --private-key KEY --tier 1 [--contract ADDR] [--dry-run]

Tiers:
    1      = 0.01 BNB
    10     = 0.1 BNB
    100    = 0.9 BNB   (10% off)
    1000   = 8.4 BNB   (16% off)
    10000  = 75 BNB    (25% off)
"""

import argparse
import json
import sys

try:
    from web3 import Web3
    from eth_account import Account
except ImportError:
    print("Error: web3 and eth-account required. Install with:", file=sys.stderr)
    print("  pip install web3 eth-account", file=sys.stderr)
    sys.exit(1)

# BSC RPC endpoints (fallback order)
BSC_RPC_URLS = [
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed1.defibit.io/",
    "https://rpc.ankr.com/bsc",
]

# Default PANdoraBox contract address (BSC mainnet)
DEFAULT_CONTRACT = "0x0000000000000000000000000000000000000000"  # TODO: set deployed address

VALID_TIERS = [1, 10, 100, 1000, 10000]

# Minimal ABI for openBox + view functions
PANDORA_BOX_ABI = json.loads("""[
    {
        "inputs": [{"name": "tier", "type": "uint256"}],
        "name": "openBox",
        "outputs": [{"name": "orderId", "type": "bytes32"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "tier", "type": "uint256"}],
        "name": "getPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getStats",
        "outputs": [
            {"name": "_totalBoxesOpened", "type": "uint256"},
            {"name": "_totalVolumeBNB", "type": "uint256"},
            {"name": "_totalOrders", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserStats",
        "outputs": [
            {"name": "boxesOpened", "type": "uint256"},
            {"name": "totalSpent", "type": "uint256"},
            {"name": "orderCount", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "orderId", "type": "bytes32"}],
        "name": "getOrder",
        "outputs": [
            {"name": "user", "type": "address"},
            {"name": "tier", "type": "uint256"},
            {"name": "amount", "type": "uint256"},
            {"name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "name": "orderId", "type": "bytes32"},
            {"indexed": true, "name": "user", "type": "address"},
            {"indexed": false, "name": "tier", "type": "uint256"},
            {"indexed": false, "name": "amount", "type": "uint256"},
            {"indexed": false, "name": "timestamp", "type": "uint256"}
        ],
        "name": "BoxOpened",
        "type": "event"
    }
]""")


def connect_bsc(rpc_urls=None):
    """Connect to BSC with RPC fallback."""
    urls = rpc_urls or BSC_RPC_URLS
    for url in urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                print(f"[+] Connected to BSC via {url}")
                return w3
        except Exception:
            continue
    print("Error: Could not connect to any BSC RPC endpoint", file=sys.stderr)
    sys.exit(1)


def normalize_key(key):
    """Normalize private key (handle 0x prefix)."""
    key = key.strip()
    if not key.startswith("0x"):
        key = "0x" + key
    return key


def open_box(private_key, tier, contract_address, dry_run=False, api_url=None):
    """Open a PANdoraBox mystery box."""
    w3 = connect_bsc()
    chain_id = 56

    # Load account
    key = normalize_key(private_key)
    account = Account.from_key(key)
    sender = account.address
    print(f"[+] Wallet: {sender}")

    # Load contract
    contract_addr = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_addr, abi=PANDORA_BOX_ABI)

    # Get price from contract
    price_wei = contract.functions.getPrice(tier).call()
    price_bnb = Web3.from_wei(price_wei, "ether")
    print(f"[+] Tier: {tier} boxes")
    print(f"[+] Price: {price_bnb} BNB ({price_wei} wei)")

    # Check balance
    balance = w3.eth.get_balance(sender)
    balance_bnb = Web3.from_wei(balance, "ether")
    print(f"[+] Balance: {balance_bnb} BNB")

    if balance < price_wei:
        print(f"\nError: Insufficient balance. Need {price_bnb} BNB, have {balance_bnb} BNB", file=sys.stderr)
        sys.exit(1)

    # Build transaction
    nonce = w3.eth.get_transaction_count(sender)

    tx = contract.functions.openBox(tier).build_transaction({
        "from": sender,
        "value": price_wei,
        "gas": 300000,  # generous limit for openBox
        "gasPrice": Web3.to_wei(3, "gwei"),  # BSC minimum
        "nonce": nonce,
        "chainId": chain_id,
    })

    # Estimate gas
    try:
        estimated_gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
        print(f"[+] Estimated gas: {estimated_gas} (using {tx['gas']})")
    except Exception as e:
        print(f"[!] Gas estimation failed, using default 300000: {e}")

    total_cost_wei = price_wei + (tx["gas"] * tx["gasPrice"])
    total_cost_bnb = Web3.from_wei(total_cost_wei, "ether")

    print(f"\n{'='*60}")
    print(f"  PANdoraBox - Open Mystery Box")
    print(f"{'='*60}")
    print(f"  Contract  : {contract_addr}")
    print(f"  From      : {sender}")
    print(f"  Tier      : {tier} box(es)")
    print(f"  Price     : {price_bnb} BNB")
    print(f"  Gas       : {tx['gas']} units @ {Web3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
    print(f"  Total Cost: ~{total_cost_bnb} BNB (price + gas)")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n[DRY RUN] Transaction validated but NOT broadcast.")
        print(f"[DRY RUN] Remove --dry-run to execute.")
        return None

    # Sign and send
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = tx_hash.hex()
    print(f"\n[+] Transaction sent: 0x{tx_hash_hex}")
    print(f"[+] BSCScan: https://bscscan.com/tx/0x{tx_hash_hex}")

    # Wait for receipt
    print("[+] Waiting for confirmation...")
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    except Exception as e:
        print(f"\n[!] Timeout waiting for receipt: {e}", file=sys.stderr)
        print(f"[!] Check manually: https://bscscan.com/tx/0x{tx_hash_hex}")
        return {"tx_hash": f"0x{tx_hash_hex}", "status": "pending"}

    if receipt["status"] == 1:
        print(f"[+] Transaction confirmed in block {receipt['blockNumber']}")
        print(f"[+] Gas used: {receipt['gasUsed']}")

        # Parse BoxOpened event to get orderId
        order_id = None
        try:
            logs = contract.events.BoxOpened().process_receipt(receipt)
            if logs:
                order_id = logs[0]["args"]["orderId"].hex()
                print(f"[+] Order ID: 0x{order_id}")
        except Exception as e:
            print(f"[!] Could not parse BoxOpened event: {e}")

        result = {
            "tx_hash": f"0x{tx_hash_hex}",
            "status": "success",
            "block": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "order_id": f"0x{order_id}" if order_id else None,
            "tier": tier,
            "price_bnb": str(price_bnb),
        }

        print(f"\n{'='*60}")
        print(f"  BOX OPENED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"  TX Hash   : {result['tx_hash']}")
        print(f"  Order ID  : {result['order_id']}")
        print(f"  Tier      : {tier}")
        print(f"  Price     : {price_bnb} BNB")
        print(f"{'='*60}")

        # TODO: Call backend API to generate image
        if api_url:
            print(f"\n[+] Calling backend API to generate image...")
            _call_generate_api(api_url, result)

        return result
    else:
        print(f"\n[!] Transaction FAILED", file=sys.stderr)
        print(f"[!] Check: https://bscscan.com/tx/0x{tx_hash_hex}")
        return {"tx_hash": f"0x{tx_hash_hex}", "status": "failed"}


def _call_generate_api(api_url, result):
    """Call backend API to generate image after successful box opening.

    API endpoint and payload format TBD.
    """
    try:
        import urllib.request
        payload = json.dumps({
            "tx_hash": result["tx_hash"],
            "order_id": result["order_id"],
            "tier": result["tier"],
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"[+] API response: {json.dumps(body, indent=2)}")
    except Exception as e:
        print(f"[!] API call failed (non-blocking): {e}", file=sys.stderr)
        print(f"[!] You can retry manually with tx_hash: {result['tx_hash']}")


def main():
    parser = argparse.ArgumentParser(description="Open a PANdoraBox mystery box on BNB Chain")
    parser.add_argument("--private-key", required=True, help="Wallet private key (hex)")
    parser.add_argument("--tier", type=int, required=True, choices=VALID_TIERS,
                        help="Number of boxes to open (1, 10, 100, 1000, 10000)")
    parser.add_argument("--contract", default=DEFAULT_CONTRACT,
                        help=f"PANdoraBox contract address (default: {DEFAULT_CONTRACT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate transaction without broadcasting")
    parser.add_argument("--api-url", default=None,
                        help="Backend API URL for image generation (optional)")
    args = parser.parse_args()

    open_box(
        private_key=args.private_key,
        tier=args.tier,
        contract_address=args.contract,
        dry_run=args.dry_run,
        api_url=args.api_url,
    )


if __name__ == "__main__":
    main()
