# PANdoraBox Skill

**name:** pandora-box
**description:** PANdoraBox mystery box skill. Open mystery boxes on BNB Chain, get AI-generated artwork, and mint SBT.
**trigger keywords:** open box, mystery box, pandora box, PANdoraBox, blind box, 盲盒, 开盲盒

## Scripts

### open_box.py — Open Mystery Box (Full Flow)

Complete 4-step flow: on-chain payment → order verification & rarity draw → AI artwork generation → SBT image binding.

**Usage:**

```bash
# Dry run (validate without broadcasting)
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 1 \
  --dry-run

# Open 1 box (0.01 BNB) — full flow
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 1

# Open 100 boxes with 10% discount (0.9 BNB)
python3 pandora-box/scripts/open_box.py \
  --private-key $PRIVATE_KEY \
  --tier 100
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--private-key` | Yes | — | Wallet private key (hex, with or without 0x) |
| `--tier` | Yes | — | Number of boxes: 1, 10, 100, 1000, or 10000 |
| `--contract` | No | `0x1Fe618B20f5fa59211d41b7bd7Ca0161573D6DD0` | PANdoraBox contract address |
| `--api-base` | No | `https://pandora.pan.network` | Backend API base URL |
| `--dry-run` | No | — | Validate without broadcasting |

**Pricing:**

| Tier | Price | Discount |
|------|-------|----------|
| 1 | 0.01 BNB | — |
| 10 | 0.1 BNB | — |
| 100 | 0.9 BNB | 10% off |
| 1000 | 8.4 BNB | 16% off |
| 10000 | 75 BNB | 25% off |

**Rarity System:**

| Rarity | Probability | Points |
|--------|-------------|--------|
| Rare | 89% | 500 |
| SR | 10% | 2,500 |
| Epic | 1% | 10,000 |

Guaranteed drops: tier 100+ → guaranteed SR, tier 1000+ → guaranteed Epic.

## Flow

```
Step 1: openBox(tier) on-chain → tx_hash
Step 2: POST /api/box/open → verify tx, draw rarity, create order + SBT
Step 3: POST /api/generate-image → AI artwork → IPFS upload → image_url
Step 4: POST /api/sbt/update-image → bind image to SBT
```

**Output:** tx_hash, order_id, rarity, points, image_url (IPFS), BSCScan link.

## Contract

- **Address:** `0x1Fe618B20f5fa59211d41b7bd7Ca0161573D6DD0`
- **Network:** BNB Chain (BSC mainnet, chain ID 56)
- **Function:** `openBox(uint256 tier) payable → bytes32 orderId`
- **Event:** `BoxOpened(bytes32 orderId, address user, uint256 tier, uint256 amount, uint256 timestamp)`
- **Website:** https://pandora.pan.network
- **BSCScan:** https://bscscan.com/address/0x1Fe618B20f5fa59211d41b7bd7Ca0161573D6DD0
