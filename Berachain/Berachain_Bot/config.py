from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Network
RPC_URL = os.getenv('RPC_URL')
CHAIN_ID = 80084

# Wallet
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# Contract addresses
WBERA_CONTRACT = "0x7507c1dc16935B82698e4C63f2746A2fCf994dF8"
BGT_CONTRACT = "0xAD57d7d39a487C04a44D3522b910421888Fb9C6d"
DELEGATE_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))