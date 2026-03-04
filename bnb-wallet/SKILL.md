---
name: bnb-wallet
description: >
  BNB Chain (BSC) wallet skill. Use this whenever the user wants to: create a
  BSC/BNB wallet, generate a private key and address, transfer BNB to another
  address, or interact with a smart contract (calling functions by name with ABI
  and arguments, including payable functions that send BNB value). Trigger
  keywords: create wallet, BNB wallet, transfer BNB, send BNB, contract call,
  contract interaction, ABI function, payable function, send BNB to contract,
  read contract, write contract. Use this skill even if the user just asks "how
  do I create a BNB wallet" or "call a contract function on BSC".
---

# BNB Chain Wallet Skill

Handles wallet management, BNB transfers, and smart contract interaction on
BNB Chain (BSC, chain_id=56).

## Dependencies

```bash
pip install web3 eth-account --break-system-packages
```

## Script Locations

All scripts live in `scripts/`. Network reference in `references/bsc_network.md`.

---

## 1. Create Wallet

**Script:** `scripts/create_wallet.py`

```bash
# Basic: generate address + private key
python3 scripts/create_wallet.py

# With 12-word mnemonic phrase
python3 scripts/create_wallet.py --mnemonic

# Save encrypted keystore file
python3 scripts/create_wallet.py --save wallet.json --password "yourpassword"
```

**Output fields:**
- `address` — BSC address (EIP-55 checksum format)
- `private_key` — raw hex private key
- `mnemonic` (optional) — 12-word BIP-39 mnemonic
- `keystore_file` (optional) — path to encrypted JSON keystore

**Notes:**
- Each call generates a fresh random wallet
- Always remind the user to back up their private key / mnemonic securely
- Use `--save + --password` when the user wants a keystore file

---

## 2. Transfer BNB

**Script:** `scripts/transfer_bnb.py`

```bash
# Standard transfer
python3 scripts/transfer_bnb.py \
  --private-key 0xYOURKEY \
  --to 0xRECIPIENT \
  --amount 0.01

# Custom gas price (BSC minimum is 3 Gwei)
python3 scripts/transfer_bnb.py \
  --private-key 0xYOURKEY \
  --to 0xRECIPIENT \
  --amount 0.5 \
  --gas-price 5

# Dry run first — simulate without broadcasting
python3 scripts/transfer_bnb.py \
  --private-key 0xYOURKEY \
  --to 0xRECIPIENT \
  --amount 1.0 \
  --dry-run

# Custom RPC endpoint
python3 scripts/transfer_bnb.py \
  --private-key 0xYOURKEY \
  --to 0xRECIPIENT \
  --amount 0.01 \
  --rpc https://bsc-dataseed.binance.org/
```

**Parameters:**
| Flag | Required | Description |
|------|----------|-------------|
| `--private-key` | ✅ | Sender's private key |
| `--to` | ✅ | Recipient address |
| `--amount` | ✅ | Amount in BNB |
| `--gas-price` | ❌ | Gas price in Gwei (default: 3) |
| `--rpc` | ❌ | Custom RPC URL |
| `--dry-run` | ❌ | Simulate, do not broadcast |

---

## 3. Contract Interaction

**Script:** `scripts/contract_call.py`

### 3a. Read Contract (view / pure)

```bash
# Query ERC20 balance
python3 scripts/contract_call.py \
  --contract 0xTOKEN_ADDRESS \
  --abi '[{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]' \
  --function balanceOf \
  --args '["0xWALLET_ADDRESS"]'

# Query totalSupply (no args)
python3 scripts/contract_call.py \
  --contract 0xTOKEN_ADDRESS \
  --abi '[{"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]' \
  --function totalSupply
```

### 3b. Write Contract (nonpayable)

```bash
python3 scripts/contract_call.py \
  --private-key 0xYOURKEY \
  --contract 0xCONTRACT \
  --abi '[{"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]' \
  --function transfer \
  --args '["0xRECIPIENT", 1000000000000000000]'
```

### 3c. Payable Function (send BNB with call)

```bash
# Call payable function and attach 0.1 BNB
python3 scripts/contract_call.py \
  --private-key 0xYOURKEY \
  --contract 0xCONTRACT \
  --abi '[{"inputs":[{"name":"minOut","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"}]' \
  --function swapExactETHForTokens \
  --args '[0, ["0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c","0xTOKEN"], "0xYOUR_ADDRESS", 9999999999]' \
  --value 0.1 \
  --gas-limit 300000 \
  --dry-run
```

### 3d. Load ABI from File

```bash
echo '[{"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]' > abi.json

python3 scripts/contract_call.py \
  --contract 0xCONTRACT \
  --abi-file abi.json \
  --function totalSupply
```

**Parameters:**
| Flag | Required | Description |
|------|----------|-------------|
| `--contract` | ✅ | Contract address |
| `--abi` or `--abi-file` | ✅ | ABI as JSON string or file path |
| `--function` | ✅ | Function name to call |
| `--args` | ❌ | JSON array of arguments |
| `--value` | ❌ | BNB to send (payable functions) |
| `--private-key` | ✅ for writes | Sender's private key |
| `--gas-limit` | ❌ | Gas limit (default: auto-estimate + 20%) |
| `--gas-price` | ❌ | Gas price in Gwei (default: 3) |
| `--dry-run` | ❌ | Simulate, do not broadcast |

---

## Workflow Guide

1. **Create wallet** → run `create_wallet.py`, display address + private key, remind user to save securely
2. **Transfer BNB** → always `--dry-run` first, then re-run without it to broadcast
3. **Contract interaction** → identify function type (view / nonpayable / payable), use `--value` for payable; always `--dry-run` write calls first

## Argument Type Coercion

The script auto-converts args based on ABI input types:
- `uint*/int*` → Python `int` (strings like `"100"` also accepted)
- `address` → EIP-55 checksum address
- `bool` → Python `bool` (`"true"` / `"false"` strings recognized)
- `address[]` / `uint256[]` → pass as JSON array

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `Insufficient balance` | Not enough BNB | Check balance; ensure enough for amount + gas |
| `Gas estimate failed` | Transaction will revert | Check args, contract state, value |
| `Function not found` | Name or ABI mismatch | Verify ABI on BSCScan |
| `Cannot connect` | RPC unreachable | Try a fallback RPC from `references/bsc_network.md` |

## Security Best Practices

- Pass private keys via env vars: `PRIVATE_KEY=0x... python3 script.py --private-key $PRIVATE_KEY`
- Always `--dry-run` before broadcasting important transactions
- Verify contract addresses on https://bscscan.com before calling
- Prefer keystore files over raw private keys in production
- See `references/bsc_network.md` for RPC list, common ABIs, and gas reference
