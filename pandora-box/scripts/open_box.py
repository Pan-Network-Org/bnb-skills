#!/usr/bin/env python3
"""
Open a PANdoraBox mystery box on BNB Chain.

Full flow:
  1. Connect to BSC & call openBox(tier) on-chain
  2. POST /api/box/open — verify tx, draw rarity, create order + SBT
  3. POST /api/generate-image — AI generates artwork, uploads to IPFS
  4. POST /api/sbt/update-image — bind image to SBT

Usage:
    python3 open_box.py --private-key KEY --tier 1 [--dry-run]

Tiers:
    1      = 0.01 BNB
    10     = 0.1 BNB
    100    = 0.9 BNB   (10% off)
    1000   = 8.4 BNB   (16% off)
    10000  = 75 BNB    (25% off)
"""

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.request
import urllib.error

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

# PANdoraBox contract (BSC mainnet)
DEFAULT_CONTRACT = "0x1Fe618B20f5fa59211d41b7bd7Ca0161573D6DD0"

# PANdora backend API
DEFAULT_API_BASE = "https://pandora.pan.network"

VALID_TIERS = [1, 10, 100, 1000, 10000]

# Minimal ABI: openBox + getPrice + BoxOpened event
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


def api_post(base_url, path, payload, timeout=120):
    """POST JSON to backend API and return parsed response."""
    url = f"{base_url}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[!] API error {e.code} on {path}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[!] API request failed on {path}: {e}", file=sys.stderr)
        return None


def download_image(url, prefix="pandora_box_"):
    """Download image from URL to a temp file. Returns local file path or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PANdoraBox-Skill/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "webp" in content_type:
                ext = ".webp"
            elif "png" in content_type:
                ext = ".png"
            elif "gif" in content_type:
                ext = ".gif"
            else:
                ext = ".jpg"
            fd, path = tempfile.mkstemp(suffix=ext, prefix=prefix)
            with os.fdopen(fd, "wb") as f:
                f.write(resp.read())
            print(f"[+] Image downloaded: {path}")
            return path
    except Exception as e:
        print(f"[!] Image download failed: {e}", file=sys.stderr)
        return None


def open_box(private_key, tier, contract_address, api_base, dry_run=False):
    """Open a PANdoraBox mystery box — full flow."""
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
    print(f"[+] Price: {price_bnb} BNB")

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
        "gas": 300000,
        "gasPrice": Web3.to_wei(3, "gwei"),
        "nonce": nonce,
        "chainId": chain_id,
    })

    # Estimate gas
    try:
        estimated_gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(estimated_gas * 1.2)
        print(f"[+] Estimated gas: {estimated_gas} (using {tx['gas']})")
    except Exception as e:
        print(f"[!] Gas estimation failed, using default 300000: {e}")

    total_cost_bnb = Web3.from_wei(price_wei + tx["gas"] * tx["gasPrice"], "ether")

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
        return None

    # ========== Step 1: On-chain transaction ==========
    print(f"\n[Step 1/4] Sending on-chain transaction...")
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = f"0x{tx_hash.hex()}"
    print(f"[+] TX sent: {tx_hash_hex}")
    print(f"[+] BSCScan: https://bscscan.com/tx/{tx_hash_hex}")

    print("[+] Waiting for confirmation...")
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    except Exception as e:
        print(f"[!] Timeout: {e}", file=sys.stderr)
        print(f"[!] Check: https://bscscan.com/tx/{tx_hash_hex}")
        return {"tx_hash": tx_hash_hex, "status": "pending"}

    if receipt["status"] != 1:
        print(f"[!] Transaction FAILED", file=sys.stderr)
        return {"tx_hash": tx_hash_hex, "status": "failed"}

    print(f"[+] Confirmed in block {receipt['blockNumber']}, gas used: {receipt['gasUsed']}")

    # Parse BoxOpened event
    order_id = None
    try:
        logs = contract.events.BoxOpened().process_receipt(receipt)
        if logs:
            order_id = f"0x{logs[0]['args']['orderId'].hex()}"
            print(f"[+] Order ID: {order_id}")
    except Exception as e:
        print(f"[!] Could not parse BoxOpened event: {e}")

    # ========== Step 2: Verify tx & create order ==========
    print(f"\n[Step 2/4] Processing order (verify tx, draw rarity)...")
    order_resp = api_post(api_base, "/api/box/open", {
        "walletAddress": sender,
        "tier": tier,
        "paymentMethod": "BNB",
        "txHash": tx_hash_hex,
        "cryptoAmount": float(price_bnb),
    })

    if not order_resp or not order_resp.get("success"):
        print(f"[!] Order processing failed. TX was successful, retry with tx_hash: {tx_hash_hex}", file=sys.stderr)
        return {"tx_hash": tx_hash_hex, "status": "tx_success_order_failed", "order_id": order_id}

    order = order_resp["order"]
    sbts = order_resp.get("sbts", [])
    highest_rarity = order.get("highestRarity", "Unknown")
    total_points = order.get("totalPoints", 0)
    stats = order.get("stats", {})

    print(f"[+] Rarity drawn: {highest_rarity}")
    print(f"[+] Total points: {total_points}")
    if stats:
        print(f"[+] Breakdown: {', '.join(f'{k}: {v}' for k, v in stats.items())}")

    sbt_id = sbts[0]["id"] if sbts else None

    # ========== Step 3: Generate AI artwork ==========
    print(f"\n[Step 3/4] Generating AI artwork (this may take a moment)...")
    image_resp = api_post(api_base, "/api/generate-image", {
        "rarity": highest_rarity,
        "tier": tier,
    }, timeout=180)

    image_url = None
    ipfs_uri = None
    ipfs_cid = None
    source_image_url = None
    content_type = None
    size_bytes = None

    image_local_path = None

    if image_resp and image_resp.get("success"):
        data = image_resp["data"]
        image_url = data.get("imageUrl")
        ipfs_uri = data.get("ipfsUri")
        ipfs_cid = data.get("ipfsCid")
        source_image_url = data.get("sourceImageUrl")
        content_type = data.get("contentType")
        size_bytes = data.get("sizeBytes")
        print(f"[+] Image generated!")
        print(f"[+] IPFS: {ipfs_uri}")
        print(f"[+] URL: {image_url}")

        # Download image locally
        print(f"[+] Downloading image...")
        image_local_path = download_image(image_url)
    else:
        print(f"[!] Image generation failed (non-blocking)", file=sys.stderr)

    # ========== Step 4: Bind image to SBT ==========
    if sbt_id and image_url:
        print(f"\n[Step 4/4] Binding image to SBT...")
        update_payload = {
            "sbtId": sbt_id,
            "imageUrl": image_url,
        }
        if ipfs_uri:
            update_payload["ipfsUri"] = ipfs_uri
        if source_image_url:
            update_payload["sourceImageUrl"] = source_image_url
        if ipfs_cid:
            update_payload["ipfsCid"] = ipfs_cid
        if content_type:
            update_payload["contentType"] = content_type
        if size_bytes:
            update_payload["sizeBytes"] = size_bytes

        sbt_resp = api_post(api_base, "/api/sbt/update-image", update_payload)
        if sbt_resp and sbt_resp.get("success"):
            print(f"[+] SBT image bound successfully!")
        else:
            print(f"[!] SBT image binding failed (non-blocking)", file=sys.stderr)
    else:
        print(f"\n[Step 4/4] Skipped (no SBT or no image)")

    # ========== Result ==========
    result = {
        "tx_hash": tx_hash_hex,
        "status": "success",
        "order_id": order_id,
        "tier": tier,
        "price_bnb": str(price_bnb),
        "highest_rarity": highest_rarity,
        "total_points": total_points,
        "rarity_stats": stats,
        "image_url": image_url,
        "image_local_path": image_local_path,
        "ipfs_uri": ipfs_uri,
        "sbt_id": sbt_id,
    }

    print(f"\n{'='*60}")
    print(f"  BOX OPENED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"  TX Hash   : {tx_hash_hex}")
    print(f"  Order ID  : {order_id}")
    print(f"  Tier      : {tier} box(es)")
    print(f"  Price     : {price_bnb} BNB")
    print(f"  Rarity    : {highest_rarity}")
    print(f"  Points    : {total_points}")
    if image_local_path:
        print(f"  Image     : {image_local_path}")
    elif image_url:
        print(f"  Image URL : {image_url}")
    if ipfs_uri:
        print(f"  IPFS      : {ipfs_uri}")
    print(f"  BSCScan   : https://bscscan.com/tx/{tx_hash_hex}")
    print(f"{'='*60}")

    # Output JSON for programmatic use
    print(f"\n[JSON] {json.dumps(result)}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Open a PANdoraBox mystery box on BNB Chain")
    parser.add_argument("--private-key", required=True, help="Wallet private key (hex)")
    parser.add_argument("--tier", type=int, required=True, choices=VALID_TIERS,
                        help="Number of boxes to open (1, 10, 100, 1000, 10000)")
    parser.add_argument("--contract", default=DEFAULT_CONTRACT,
                        help=f"PANdoraBox contract address (default: {DEFAULT_CONTRACT})")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE,
                        help=f"Backend API base URL (default: {DEFAULT_API_BASE})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate transaction without broadcasting")
    args = parser.parse_args()

    open_box(
        private_key=args.private_key,
        tier=args.tier,
        contract_address=args.contract,
        api_base=args.api_base,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
