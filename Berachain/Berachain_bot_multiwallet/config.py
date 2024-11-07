from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Network
RPC_URL = os.getenv('RPC_URL')
CHAIN_ID = 80084

# Load all private keys
PRIVATE_KEYS = []
i = 1
while True:
    pk = os.getenv(f'PRIVATE_KEY_{i}')
    if pk is None:
        break
    PRIVATE_KEYS.append(pk)
    i += 1

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))