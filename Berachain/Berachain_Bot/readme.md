# Berachain bot

A Python-based tool for TEHEEE

## Requirements

- **150 Bera**
- **HONEY-WBERA LP**: Add liquidity on [Bartio Pools](https://bartio.bex.berachain.com/pools?pool=allPools).
- **800ish stgUSDC** for minting.

## Features

- Unwraps and wraps 100 Beras
- Claims BGT from LPs and delegates to validators
- Mints Honey using stgUSDC on [Bartio Honey](https://bartio.honey.berachain.com/)
   - Mint 1 Honey at a time
- Supplies Honey to [Bartio Bend](https://bartio.bend.berachain.com/)
   - Supply 1 Honey at a time

---

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/0xGery/Bot/tree/main/Berachain/Berachain_Bot
   cd Berachain_Bot
2. **Create and activate a virtual environment (recommended):**
- On Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
- On UNIX/Macos:
   ```bash
   python -m venv venv
   source venv/bin/activate
3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
4. **Create a .env file in the root directory with your private key (without the 0x prefix):**
   ```bash
   PRIVATE_KEY=your_private_key_here

## Configuration
Create a requirements.txt file with these dependencies:
   ```bash
   web3==6.11.1
   python-dotenv==1.0.0
   eth-abi==4.2.1
   ```

## Usage
Run the main script to start:
   ```bash
   python main.py
   ```

## Security Notes
- Do not commit your .env file or expose your private key
- Add .env to your .gitignore file
- Verify contract addresses before interacting

## Contributing
- Fork the repository
- Create a new branch
- Make your changes
- Submit a pull request
