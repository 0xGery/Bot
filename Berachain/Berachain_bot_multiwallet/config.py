from web3 import Web3
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Network Configuration
RPC_URLS = [
    os.getenv('RPC_URL', 'https://bartio.rpc.berachain.com'),
    os.getenv('RPC_URL_BACKUP_1', 'https://bartio.drpc.org'),
    os.getenv('RPC_URL_BACKUP_2', 'https://bera-testnet.nodeinfra.com')
]
CHAIN_ID = 80084  # Berachain Artio testnet

def get_working_web3():
    """Get a working Web3 instance by trying different RPCs"""
    random.shuffle(RPC_URLS)  # Randomize RPC order
    
    for rpc_url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
            if w3.is_connected():
                print(f"✅ Connected to RPC: {rpc_url}")
                return w3
        except Exception as e:
            print(f"❌ Failed to connect to {rpc_url}: {str(e)}")
            continue
    
    return None

def rotate_rpc():
    """Rotate to next available RPC on any error"""
    global w3
    print("\n🔄 Rotating RPC due to error...")
    w3 = get_working_web3()
    return w3 is not None

# Initialize Web3
w3 = get_working_web3()
if not w3:
    print("❌ Failed to connect to any RPC endpoint")

# Load private keys
PRIVATE_KEYS = []
i = 1
while True:
    pk = os.getenv(f'PRIVATE_KEY_{i}')
    if pk is None:
        break
    PRIVATE_KEYS.append(pk)
    i += 1
