import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode

# Contract addresses
from constants import HONEY_MINT_CONTRACT, STGUSDC_CONTRACT, GAS_LIMIT, CHAIN_ID, HONEY_ABI, ERC20_ABI


def mint_honey(amount=3000000, wallet_index=0, retry_count=0):
    """Mint HONEY tokens from STGUSDC (3000000 = 3 STGUSDC)"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        print("\n🍯 MINTING HONEY:")
        print("-"*30)
        
        contract = w3.eth.contract(address=HONEY_MINT_CONTRACT, abi=HONEY_ABI)
        
        transaction = contract.functions.mint(
            STGUSDC_CONTRACT,
            amount,  # 3000000 = 3 STGUSDC
            address
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': GAS_LIMIT,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"🔄 Minting HONEY with {amount/1000000} STGUSDC...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Mint successful! Gas used: {receipt['gasUsed']}")
        
        return True
            
    except Exception as e:
        print(f"❌ Mint error: {str(e)}")
        if rotate_rpc():
            return mint_honey(amount, wallet_index, retry_count + 1)
        return False

# Test execution
if __name__ == "__main__":
    print("Testing HONEY minting functionality...")
    try:
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            wallet_index = 0
            address = wallet_manager.get_address(wallet_index)
            print(f"Testing with wallet {wallet_index + 1} ({address})")
            
            # Test mint with 3 STGUSDC (3000000 units considering decimals)
            mint_honey(3000000, wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")
