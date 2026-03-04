# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Skill package (`bnb-wallet.skill`) for BNB Chain (BSC) blockchain operations. The `.skill` file is a ZIP archive containing Python CLI scripts for wallet creation, BNB transfers, and smart contract interaction.

## Package Structure

The skill archive contains:
- `bnb-wallet/SKILL.md` — Skill manifest (name, description, trigger keywords) and full usage docs
- `bnb-wallet/scripts/create_wallet.py` — Generate BSC wallets (address + private key, optional mnemonic/keystore)
- `bnb-wallet/scripts/transfer_bnb.py` — Transfer BNB between addresses
- `bnb-wallet/scripts/contract_call.py` — Read/write smart contract functions (view, nonpayable, payable)
- `bnb-wallet/references/bsc_network.md` — RPC endpoints, chain info, gas reference, common ABIs

## Working with the Skill Archive

```bash
# Extract for editing
unzip bnb-wallet.skill -d /tmp/bnb-extract

# Repackage after changes (from the extracted directory)
cd /tmp/bnb-extract && zip -r /path/to/bnb-wallet.skill bnb-wallet/
```

## Dependencies

```bash
pip install web3 eth-account --break-system-packages
```

Python 3 with `web3>=6.0` and `eth-account`. No build system, test framework, or linter is configured.

## Running Scripts

Scripts are standalone CLI tools run directly with `python3`:

```bash
python3 scripts/create_wallet.py [--mnemonic] [--save FILE --password PASS]
python3 scripts/transfer_bnb.py --private-key KEY --to ADDR --amount 0.01 [--dry-run]
python3 scripts/contract_call.py --contract ADDR --abi JSON --function NAME [--args JSON] [--dry-run]
```

## Key Patterns

- **RPC fallback**: Scripts try multiple BSC RPC URLs in sequence (`BSC_RPC_URLS` list) before failing
- **Dry-run**: All transaction scripts support `--dry-run` to validate everything without broadcasting — always use this first
- **ABI type coercion**: `contract_call.py` auto-converts CLI args to proper Python types based on ABI input types (uint→int, address→checksum, bool→bool)
- **Gas defaults**: 3 Gwei price (BSC minimum), 21k gas for transfers, auto-estimate with 20% buffer for contract calls
- **Private key normalization**: All scripts handle keys with or without `0x` prefix

## BSC Network Defaults

- Chain ID: 56 (mainnet), 97 (testnet)
- Block time: ~3 seconds
- Explorer: https://bscscan.com
- Testnet RPC: `https://data-seed-prebsc-1-s1.binance.org:8545/`
