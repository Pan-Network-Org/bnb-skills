# bnb-skills

BNB Chain (BSC) skill packages for [Pan Network](https://github.com/pan-network-labs). Provides CLI tools for wallet operations, BNB transfers, smart contract interaction, and PANdoraBox mystery boxes.

## Skills

| Skill | Description |
|-------|-------------|
| [`bnb-wallet`](bnb-wallet/) | Wallet creation, BNB transfers, smart contract calls |
| [`pandora-box`](pandora-box/) | PANdoraBox mystery box — open boxes on-chain |

## Quick Start

### Install Dependencies

```bash
pip install web3 eth-account
```

### Create a Wallet

```bash
python3 bnb-wallet/scripts/create_wallet.py

# With mnemonic phrase
python3 bnb-wallet/scripts/create_wallet.py --mnemonic

# Save encrypted keystore
python3 bnb-wallet/scripts/create_wallet.py --save wallet.json --password "yourpassword"
```

### Transfer BNB

```bash
# Dry run first (recommended)
python3 bnb-wallet/scripts/transfer_bnb.py \
  --private-key $PRIVATE_KEY \
  --to 0xRECIPIENT \
  --amount 0.01 \
  --dry-run

# Broadcast
python3 bnb-wallet/scripts/transfer_bnb.py \
  --private-key $PRIVATE_KEY \
  --to 0xRECIPIENT \
  --amount 0.01
```

### Smart Contract Interaction

```bash
# Read (view/pure) — no private key needed
python3 bnb-wallet/scripts/contract_call.py \
  --contract 0xTOKEN_ADDRESS \
  --abi '[{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]' \
  --function balanceOf \
  --args '["0xWALLET_ADDRESS"]'

# Write — requires private key
python3 bnb-wallet/scripts/contract_call.py \
  --private-key $PRIVATE_KEY \
  --contract 0xCONTRACT \
  --abi '[{"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]' \
  --function transfer \
  --args '["0xRECIPIENT", 1000000000000000000]' \
  --dry-run
```

### Open PANdoraBox

```bash
# Dry run first
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 1 \
  --contract 0xCONTRACT_ADDRESS \
  --dry-run

# Open 1 box (0.01 BNB)
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 1 \
  --contract 0xCONTRACT_ADDRESS
```

**Tiers:** 1 (0.01 BNB) · 10 (0.1 BNB) · 100 (0.9 BNB, 10% off) · 1000 (8.4 BNB, 16% off) · 10000 (75 BNB, 25% off)

## Network Reference

See [`bnb-wallet/references/bsc_network.md`](bnb-wallet/references/bsc_network.md) for RPC endpoints, gas reference, and common ABIs (ERC20, PancakeSwap Router).

## Security

- Always use `--dry-run` before broadcasting transactions
- Pass private keys via environment variables, not CLI args directly
- Verify contract addresses on [BSCScan](https://bscscan.com) before interacting
- Back up private keys and mnemonic phrases securely

## License

MIT
