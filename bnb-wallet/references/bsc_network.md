# BSC Network Reference

## RPC Endpoints

| Provider     | URL                                        | Notes           |
|--------------|--------------------------------------------|-----------------|
| Binance 1    | https://bsc-dataseed.binance.org/          | Official        |
| Binance 2    | https://bsc-dataseed1.binance.org/         | Official        |
| DefiKit      | https://bsc-dataseed1.defibit.io/          | Reliable        |
| Ankr         | https://rpc.ankr.com/bsc                  | Rate limited    |
| NodeReal     | https://bsc-mainnet.nodereal.io/v1/...    | API key needed  |

**Testnet:** https://data-seed-prebsc-1-s1.binance.org:8545/

## Chain Info
- Chain ID: 56 (mainnet), 97 (testnet)
- Native token: BNB
- Block time: ~3 seconds
- Explorer: https://bscscan.com

## Gas
- Minimum gas price: 3 Gwei (BSC enforced minimum)
- Simple transfer gas: 21,000
- ERC20 transfer: ~65,000
- Complex contract: 100,000 – 500,000+

## Common ABIs

### ERC20 (minimal)
```json
[
  {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"}
]
```

### PancakeSwap Router (key functions)
```json
[
  {
    "name": "swapExactETHForTokens",
    "type": "function",
    "stateMutability": "payable",
    "inputs": [
      {"name":"amountOutMin","type":"uint256"},
      {"name":"path","type":"address[]"},
      {"name":"to","type":"address"},
      {"name":"deadline","type":"uint256"}
    ],
    "outputs":[{"name":"amounts","type":"uint256[]"}]
  }
]
```

## Security Notes
- Always use `--dry-run` first before sending real transactions
- Store private keys in environment variables, not command line args (shell history)
- Use `PRIVATE_KEY=0x... python3 script.py` pattern in production
- Keystore files (encrypted JSON) are safer than raw private keys
- Verify contract addresses on BSCScan before interacting
