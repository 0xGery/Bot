# Berachain Multi-Wallet Bot

A Python bot for automating interactions with Berachain testnet, including BERA wrapping/unwrapping, HONEY minting, lending, and BGT staking/claiming.

## Requirements

- **150 Bera for wraps & unwraps**
- **HONEY-WBERA LP**: Add liquidity on [Bartio Pools](https://bartio.bex.berachain.com/pools?pool=allPools).
- **800ish stgUSDC** for minting HONEY.

## Features

- Multi-wallet support
- BERA wrapping/unwrapping
- HONEY minting with STGUSDC
- HONEY lending
- BGT claiming and delegation
- Automatic RPC rotation
- Transaction retry mechanism
- Balance tracking

## Prerequisites

- Python 3.9+
- pip (Python package installer)
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/0xGery/Bot.git
   cd Bot/Berachain/Berachain_bot_multiwallet
2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
3. Install required packages:
   ```bash
   pip install web3 eth-abi python-dotenv
4. Create `.env` file in the root directory:
   ```bash
   PRIVATE_KEY_1=your_private_key_1
   PRIVATE_KEY_2=your_private_key_2
  Add more private keys as needed
## Usage

1. Run the main bot:
    ```bash
    python3 main_multi.py
2. Test individual functions:
    ```bash
    python3 functions/wrap.py
    python3 functions/honey.py
    python3 functions/lending.py
    python3 functions/claim.py
    python3 functions/delegate.py

### BERA Wrapping/Unwrapping
- Wraps random amount (50-100 BERA)
- Automatically unwraps all WBERA
- Includes balance checks and gas estimation

### HONEY Minting
- Mints HONEY using STGUSDC
- Includes approval checks
- Balance verification

### HONEY Lending
- Supplies HONEY to lending protocol
- Automatic approval process
- Balance tracking

### BGT Management
- Claims BGT rewards
- Delegates BGT to validator
- Tracks delegation history
- Manages boost activation

## Error Handling

- Automatic RPC rotation on errors
- Maximum 3 retries per operation
- Detailed error logging
- Balance verification before transactions

## Security Notes
- Do not commit your .env file or expose your private key
- Add .env to your .gitignore file
- Verify contract addresses before interacting

## Contributing
- Fork the repository
- Create a new branch
- Make your changes
- Submit a pull request
