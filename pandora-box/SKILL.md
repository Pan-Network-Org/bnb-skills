# PANdoraBox Skill

**name:** pandora-box
**description:** PANdoraBox mystery box skill. Open mystery boxes on BNB Chain, track orders, and trigger image generation.
**trigger keywords:** open box, mystery box, pandora box, PANdoraBox, blind box, 盲盒, 开盲盒

## Scripts

### open_box.py — Open Mystery Box

Opens a PANdoraBox on BNB Chain by calling the `openBox(tier)` payable function.

**Usage:**

```bash
# Dry run (validate without broadcasting)
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

# Open 100 boxes with 10% discount (0.9 BNB)
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 100 \
  --contract 0xCONTRACT_ADDRESS

# With backend API callback for image generation
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 1 \
  --contract 0xCONTRACT_ADDRESS \
  --api-url https://api.example.com/generate
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--private-key` | Yes | Wallet private key (hex, with or without 0x) |
| `--tier` | Yes | Number of boxes: 1, 10, 100, 1000, or 10000 |
| `--contract` | No | PANdoraBox contract address |
| `--dry-run` | No | Validate without broadcasting |
| `--api-url` | No | Backend API URL for image generation |

**Pricing:**

| Tier | Price | Discount |
|------|-------|----------|
| 1 | 0.01 BNB | — |
| 10 | 0.1 BNB | — |
| 100 | 0.9 BNB | 10% off |
| 1000 | 8.4 BNB | 16% off |
| 10000 | 75 BNB | 25% off |

**Output:**

On success, returns tx_hash, order_id, tier, and price. If `--api-url` is provided, POSTs `{tx_hash, order_id, tier}` to the backend to trigger image generation.

## Contract

- **Contract:** PANdoraBox (PANdoraBoxV2.sol)
- **Network:** BNB Chain (BSC mainnet, chain ID 56)
- **Key function:** `openBox(uint256 tier) payable returns (bytes32 orderId)`
- **Event:** `BoxOpened(bytes32 orderId, address user, uint256 tier, uint256 amount, uint256 timestamp)`
