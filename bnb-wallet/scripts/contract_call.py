#!/usr/bin/env python3
"""
Interact with a smart contract on BNB Chain.
Supports read (call) and write (send) functions, with optional BNB value.

Usage:
    # Read-only call
    python3 contract_call.py \
        --contract 0xCONTRACT \
        --abi '[{"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}]' \
        --function totalSupply

    # Write transaction (payable with BNB)
    python3 contract_call.py \
        --private-key 0xYOURKEY \
        --contract 0xCONTRACT \
        --abi '[...]' \
        --function deposit \
        --args '["0xRecipient", 100]' \
        --value 0.05 \
        --gas-limit 200000

Options:
    --private-key   Sender's private key (required for write functions)
    --contract      Contract address
    --abi           ABI JSON string (array or single function object)
    --abi-file      Path to ABI JSON file (alternative to --abi)
    --function      Function name to call
    --args          JSON array of arguments e.g. '["0xAddr", 100, true]'
    --value         BNB to send with transaction (for payable functions)
    --gas-limit     Gas limit (default: auto-estimate)
    --gas-price     Gas price in Gwei (default: 3)
    --rpc           Custom RPC URL
    --dry-run       Simulate without broadcasting
"""

import argparse
import json
import sys
from decimal import Decimal
from web3 import Web3


BSC_RPC_URLS = [
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed1.defibit.io/",
    "https://rpc.ankr.com/bsc",
]


def connect(rpc_url=None):
    urls = [rpc_url] if rpc_url else BSC_RPC_URLS
    for url in urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                print(f"[✓] Connected: {url} (chain_id={w3.eth.chain_id})")
                return w3
        except Exception:
            continue
    print("Error: Cannot connect to BSC RPC.", file=sys.stderr)
    sys.exit(1)


def load_abi(abi_str=None, abi_file=None):
    """Load ABI and ensure it's a list."""
    if abi_file:
        with open(abi_file) as f:
            abi = json.load(f)
    elif abi_str:
        abi = json.loads(abi_str)
    else:
        print("Error: --abi or --abi-file required", file=sys.stderr)
        sys.exit(1)

    # If user passed a single function object, wrap it
    if isinstance(abi, dict):
        abi = [abi]
    return abi


def parse_args_for_function(func_abi, raw_args):
    """Parse raw JSON args and coerce types based on ABI inputs."""
    if not raw_args:
        return []

    args = json.loads(raw_args)
    inputs = func_abi.get("inputs", [])

    if len(args) != len(inputs):
        print(f"Warning: Function expects {len(inputs)} args, got {len(args)}", file=sys.stderr)

    coerced = []
    for i, (arg, inp) in enumerate(zip(args, inputs)):
        t = inp.get("type", "")
        if t.startswith("uint") or t.startswith("int"):
            coerced.append(int(arg))
        elif t == "bool":
            if isinstance(arg, str):
                coerced.append(arg.lower() in ("true", "1", "yes"))
            else:
                coerced.append(bool(arg))
        elif t == "address":
            coerced.append(Web3.to_checksum_address(arg))
        elif t.endswith("[]"):
            coerced.append(arg)  # Pass arrays as-is
        else:
            coerced.append(arg)
    return coerced


def is_view_function(func_abi):
    return func_abi.get("stateMutability") in ("view", "pure")


def contract_interact(
    contract_address,
    abi,
    function_name,
    args=None,
    private_key=None,
    value_bnb=0,
    gas_limit=None,
    gas_price_gwei=3,
    rpc_url=None,
    dry_run=False,
):
    w3 = connect(rpc_url)

    contract_checksum = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_checksum, abi=abi)

    # Find function ABI
    func_abi = next(
        (f for f in abi if f.get("type") == "function" and f.get("name") == function_name),
        None,
    )
    if not func_abi:
        available = [f["name"] for f in abi if f.get("type") == "function"]
        print(f"Error: Function '{function_name}' not found in ABI.", file=sys.stderr)
        print(f"Available functions: {available}", file=sys.stderr)
        sys.exit(1)

    parsed_args = parse_args_for_function(func_abi, args)

    print(f"\n{'='*60}")
    print(f"  Contract Interaction")
    print(f"{'='*60}")
    print(f"  Contract : {contract_checksum}")
    print(f"  Function : {function_name}")
    print(f"  Args     : {parsed_args}")
    print(f"  Type     : {'READ (call)' if is_view_function(func_abi) else 'WRITE (send)'}")
    if value_bnb:
        print(f"  Value    : {value_bnb} BNB")
    print(f"{'='*60}")

    # READ: call without signing
    if is_view_function(func_abi):
        func = contract.functions[function_name](*parsed_args)
        result = func.call()
        print(f"\n[✓] Result: {result}\n")
        return result

    # WRITE: requires private key
    if not private_key:
        print("Error: --private-key required for write functions.", file=sys.stderr)
        sys.exit(1)

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    account = w3.eth.account.from_key(private_key)
    sender = account.address

    balance_wei = w3.eth.get_balance(sender)
    print(f"  Sender   : {sender}")
    print(f"  Balance  : {float(w3.from_wei(balance_wei, 'ether')):.6f} BNB")

    value_wei = w3.to_wei(Decimal(str(value_bnb)), "ether") if value_bnb else 0
    gas_price_wei = w3.to_wei(gas_price_gwei, "gwei")

    tx_params = {
        "from": sender,
        "gasPrice": gas_price_wei,
        "value": value_wei,
        "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(sender, "pending"),
    }

    func = contract.functions[function_name](*parsed_args)

    # Estimate gas
    if gas_limit:
        tx_params["gas"] = gas_limit
    else:
        try:
            estimated = func.estimate_gas(tx_params)
            tx_params["gas"] = int(estimated * 1.2)  # 20% buffer
            print(f"  Gas Est. : {estimated} → using {tx_params['gas']}")
        except Exception as e:
            print(f"  Gas Estimate failed: {e}", file=sys.stderr)
            print("  Hint: The transaction may revert. Check your args and contract state.")
            sys.exit(1)

    fee_bnb = w3.from_wei(tx_params["gas"] * gas_price_wei, "ether")
    print(f"  Gas Fee  : ~{float(fee_bnb):.6f} BNB")

    if dry_run:
        print("\n[DRY RUN] Transaction NOT broadcast. All checks passed ✓\n")
        return None

    tx = func.build_transaction(tx_params)
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hex = tx_hash.hex()

    print(f"\n[✓] Transaction sent!")
    print(f"  TX Hash : {tx_hex}")
    print(f"  BSCScan : https://bscscan.com/tx/{tx_hex}")

    print("\n  Waiting for confirmation...", end="", flush=True)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    status = "✅ Success" if receipt["status"] == 1 else "❌ Reverted"
    print(f"\n  Status  : {status}")
    print(f"  Block   : {receipt['blockNumber']}")
    print(f"  Gas Used: {receipt['gasUsed']}")
    print(f"{'='*60}\n")

    return tx_hex


def main():
    parser = argparse.ArgumentParser(description="Interact with BSC smart contracts")
    parser.add_argument("--private-key", help="Sender private key (write functions only)")
    parser.add_argument("--contract", required=True, help="Contract address")
    parser.add_argument("--abi", help="ABI JSON string")
    parser.add_argument("--abi-file", help="Path to ABI JSON file")
    parser.add_argument("--function", required=True, dest="function_name", help="Function name")
    parser.add_argument("--args", default=None, help='JSON array of args e.g. \'["0xAddr", 100]\'')
    parser.add_argument("--value", type=float, default=0, help="BNB to send (payable functions)")
    parser.add_argument("--gas-limit", type=int, default=None, help="Gas limit override")
    parser.add_argument("--gas-price", type=float, default=3.0, help="Gas price in Gwei")
    parser.add_argument("--rpc", default=None, help="Custom RPC URL")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without broadcasting")
    args = parser.parse_args()

    abi = load_abi(args.abi, args.abi_file)

    contract_interact(
        contract_address=args.contract,
        abi=abi,
        function_name=args.function_name,
        args=args.args,
        private_key=args.private_key,
        value_bnb=args.value,
        gas_limit=args.gas_limit,
        gas_price_gwei=args.gas_price,
        rpc_url=args.rpc,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
