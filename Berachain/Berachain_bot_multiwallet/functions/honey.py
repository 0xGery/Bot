import sys
import os
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode

# Contract addresses
from constants import HONEY_MINT_CONTRACT, STGUSDC_CONTRACT, GAS_LIMIT, CHAIN_ID, HONEY_ABI, ERC20_ABI


def mint_honey(wallet_index=0, retry_count=0):
    """Mint HONEY tokens from STGUSDC (random amount between 3-5 STGUSDC)"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        # Validate wallet index
        if not wallet_manager.is_valid_index(wallet_index):
            print(f"❌ Invalid wallet index: {wallet_index}")
            return False

        # Randomly choose amount between 3, 4, or 5 STGUSDC
        stg_amount = random.choice([3, 4, 5])
        amount = stg_amount * 1000000  # Convert to STGUSDC units (6 decimals)
        
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)

        # Verify STGUSDC balance before minting
        stgusdc_contract = w3.eth.contract(address=STGUSDC_CONTRACT, abi=ERC20_ABI)
        stgusdc_balance = stgusdc_contract.functions.balanceOf(address).call()
        
        if stgusdc_balance < amount:
            print(f"❌ Insufficient STGUSDC balance. Required: {stg_amount}, Available: {stgusdc_balance/1000000}")
            return False
        
        print("\n🍯 MINTING HONEY:")
        print("-"*30)
        print(f"📊 STGUSDC Balance: {stgusdc_balance/1000000}")
        print(f"🎯 Attempting to mint with {stg_amount} STGUSDC")
        
        # Check allowance and approve if needed
        allowance = stgusdc_contract.functions.allowance(address, HONEY_MINT_CONTRACT).call()
        if allowance < amount:
            print("\n✍️  Approving STGUSDC:")
            approve_txn = stgusdc_contract.functions.approve(
                HONEY_MINT_CONTRACT,
                amount
            ).build_transaction({
                'from': address,
                'nonce': w3.eth.get_transaction_count(address),
                'gas': GAS_LIMIT,
                'gasPrice': w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            
            signed_txn = w3.eth.account.sign_transaction(approve_txn, account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"📝 Approval Tx Hash: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Approval successful! Gas used: {receipt['gasUsed']}")
            random_delay(5, 10)
        
        contract = w3.eth.contract(address=HONEY_MINT_CONTRACT, abi=HONEY_ABI)
        
        transaction = contract.functions.mint(
            STGUSDC_CONTRACT,
            amount,
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
        print(f"🔄 Minting HONEY with {stg_amount} STGUSDC...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Mint successful! Gas used: {receipt['gasUsed']}")
        
        return True
            
    except Exception as e:
        print(f"❌ Mint error: {str(e)}")
        if rotate_rpc():
            return mint_honey(wallet_index, retry_count + 1)
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
            
            # Test mint with random amount between 3-5 STGUSDC
            mint_honey(wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")
