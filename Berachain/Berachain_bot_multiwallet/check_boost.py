from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
RPC_URLS = [
    os.getenv('RPC_URL'),
    os.getenv('RPC_URL_BACKUP_1'),
    os.getenv('RPC_URL_BACKUP_2')
]
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"
VALIDATOR_ADDRESS = "0x40495A781095932e2FC8dccA69F5e358711Fdd41"

# Get wallet addresses from private keys
PRIVATE_KEYS = [
    os.getenv('PRIVATE_KEY_1'),
    os.getenv('PRIVATE_KEY_2')
]

# Updated ABI with correct function signatures
ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "queuedBoost",
        "outputs": [{"type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "unboostedBalanceOf",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "validator", "type": "address"}
        ],
        "name": "boosted",
        "outputs": [{"type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "validator", "type": "address"}
        ],
        "name": "boostedQueue",
        "outputs": [
            {"name": "blockNumberLast", "type": "uint32"},
            {"name": "balance", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_address_from_private_key(w3, private_key):
    """Get wallet address from private key"""
    account = w3.eth.account.from_key(private_key)
    return account.address

def check_balances(w3, wallet_address, index):
    """Check all BGT-related balances for a wallet"""
    try:
        # Initialize contract
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=ABI)
        
        # Convert addresses to checksum
        wallet = w3.to_checksum_address(wallet_address)
        validator = w3.to_checksum_address(VALIDATOR_ADDRESS)
        current_block = w3.eth.block_number
        
        # Get all balances
        total_balance = contract.functions.balanceOf(wallet).call()
        unboosted_balance = contract.functions.unboostedBalanceOf(wallet).call()
        queued_boost = contract.functions.queuedBoost(wallet).call()
        boosted_amount = contract.functions.boosted(wallet, validator).call()
        queue_info = contract.functions.boostedQueue(wallet, validator).call()
        
        # Print results
        print(f"\n🔍 Wallet {index + 1} Status:")
        print(f"├─ Address: {wallet}")
        print(f"├─ Current Block: {current_block}")
        print(f"├─ Total Balance: {w3.from_wei(total_balance, 'ether')} BGT")
        print(f"├─ Unboosted Balance: {w3.from_wei(unboosted_balance, 'ether')} BGT")
        print(f"├─ Total Queued: {w3.from_wei(queued_boost, 'ether')} BGT")
        print(f"├─ Boosted with Validator: {w3.from_wei(boosted_amount, 'ether')} BGT")
        print(f"├─ Queue Block Number: {queue_info[0]}")
        print(f"└─ Queue Balance: {w3.from_wei(queue_info[1], 'ether')} BGT")
        
    except Exception as e:
        print(f"❌ Error checking wallet {index + 1}: {str(e)}")

def main():
    """Main function to check all wallets"""
    # Try each RPC URL until one works
    w3 = None
    for rpc_url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                print(f"✅ Connected to RPC: {rpc_url}")
                print(f"📦 Current block: {w3.eth.block_number}")
                break
        except Exception:
            continue
    
    if not w3 or not w3.is_connected():
        print("❌ Failed to connect to any RPC")
        return
        
    # Check each wallet
    for i, private_key in enumerate(PRIVATE_KEYS):
        if private_key:
            wallet_address = get_address_from_private_key(w3, private_key)
            check_balances(w3, wallet_address, i)
        else:
            print(f"❌ No private key found for wallet {i + 1}")

if __name__ == "__main__":
    main()
