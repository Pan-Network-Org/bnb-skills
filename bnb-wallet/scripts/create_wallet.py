#!/usr/bin/env python3
"""
Create a new BNB Chain (BSC) local wallet.
Generates a random private key, derives address, and saves to keyfile.

Usage:
    python3 create_wallet.py [--save keyfile.json] [--password yourpassword]

Output:
    - Address
    - Private key (hex)
    - Optional: encrypted keystore JSON file
"""

import argparse
import json
import sys
import os
from eth_account import Account

Account.enable_unaudited_hdwallet_features()


def create_wallet(save_path=None, password=None, mnemonic=False):
    if mnemonic:
        acct, mnemonic_phrase = Account.create_with_mnemonic()
    else:
        acct = Account.create()
        mnemonic_phrase = None

    result = {
        "address": acct.address,
        "private_key": acct.key.hex(),
    }
    if mnemonic_phrase:
        result["mnemonic"] = mnemonic_phrase

    if save_path and password:
        keystore = Account.encrypt(acct.key, password)
        with open(save_path, "w") as f:
            json.dump(keystore, f, indent=2)
        result["keystore_file"] = os.path.abspath(save_path)
        print(f"[✓] Keystore saved to: {result['keystore_file']}")

    print(f"\n{'='*60}")
    print(f"  BNB Chain Wallet Created")
    print(f"{'='*60}")
    print(f"  Address     : {result['address']}")
    print(f"  Private Key : {result['private_key']}")
    if mnemonic_phrase:
        print(f"  Mnemonic    : {mnemonic_phrase}")
    print(f"{'='*60}")
    print(f"  ⚠️  KEEP YOUR PRIVATE KEY / MNEMONIC SAFE!")
    print(f"  ⚠️  Never share it with anyone.")
    print(f"{'='*60}\n")

    return result


def main():
    parser = argparse.ArgumentParser(description="Create a new BNB Chain wallet")
    parser.add_argument("--save", metavar="FILE", help="Save encrypted keystore to file")
    parser.add_argument("--password", metavar="PASS", help="Password for keystore encryption")
    parser.add_argument("--mnemonic", action="store_true", help="Generate with mnemonic phrase")
    args = parser.parse_args()

    if args.save and not args.password:
        print("Error: --password required when --save is specified", file=sys.stderr)
        sys.exit(1)

    create_wallet(
        save_path=args.save,
        password=args.password,
        mnemonic=args.mnemonic
    )


if __name__ == "__main__":
    main()
