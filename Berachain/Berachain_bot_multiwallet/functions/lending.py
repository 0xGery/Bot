import sys
import os
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode
from web3 import Web3

# Contract addresses
from constants import LENDING_CONTRACT, HONEY_TOKEN, LENDING_ABI, ERC20_ABI, GAS_LIMIT, CHAIN_ID

def check_and_approve_honey(amount, wallet_index=0, retry_count=0):
    """Check HONEY balance and approve if needed"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        honey_contract = w3.eth.contract(address=HONEY_TOKEN, abi=ERC20_ABI)
        
        balance = honey_contract.functions.balanceOf(address).call()
        print("\n🍯 HONEY Balance Check:")
        print(f"└─ Current Balance: {w3.from_wei(balance, 'ether')} HONEY")
        
        if balance < amount:
            print("❌ Insufficient HONEY balance")
            return False
            
        allowance = honey_contract.functions.allowance(address, LENDING_CONTRACT).call()
        if allowance < amount:
            print("\n✍️  Approving HONEY:")
            print("-"*30)
            
            approve_txn = honey_contract.functions.approve(
                LENDING_CONTRACT,
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
            print(f"📝 Tx Hash: {tx_hash.hex()}")
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Approval successful! Gas used: {receipt['gasUsed']}")
            
            random_delay(5, 10)
            
        return True
            
    except Exception as e:
        print(f"❌ Approval error: {str(e)}")
        if rotate_rpc():
            return check_and_approve_honey(amount, wallet_index, retry_count + 1)
        return False

def supply_honey(wallet_index=0, retry_count=0):
    """Supply random amount of HONEY (1, 2, or 3) to lending protocol"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        # Randomly choose amount between 1, 2, or 3 HONEY
        amount_in_honey = random.choice([1, 2, 3])
        
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        amount_in_wei = w3.to_wei(amount_in_honey, 'ether')
        
        print("\n📥 SUPPLYING HONEY:")
        print("-"*30)
        
        if not check_and_approve_honey(amount_in_wei, wallet_index):
            return False
            
        contract = w3.eth.contract(address=LENDING_CONTRACT, abi=LENDING_ABI)
        
        transaction = contract.functions.supply(
            HONEY_TOKEN,
            amount_in_wei,
            address,
            18
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': GAS_LIMIT,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"🔄 Supplying {amount_in_honey} HONEY...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Supply successful! Gas used: {receipt['gasUsed']}")
        
        return True
            
    except Exception as e:
        print(f"❌ Supply error: {str(e)}")
        if rotate_rpc():
            return supply_honey(wallet_index, retry_count + 1)
        return False

# Alternative raw method implementation
def supply_honey_raw(wallet_index=0):
    """Supply random amount of HONEY (1, 2, or 3) to lending protocol using raw transaction"""
    try:
        # Randomly choose amount between 1, 2, or 3 HONEY
        amount_in_honey = random.choice([1, 2, 3])
        
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        # Convert amount to Wei (18 decimals)
        amount_in_wei = w3.to_wei(amount_in_honey, 'ether')
        
        # First check and approve HONEY
        if not check_and_approve_honey(amount_in_wei, wallet_index):
            return False
            
        # Method ID for supply(address,uint256,address,uint16)
        method_id = "0x617ba037"
        
        # Encode parameters
        params = encode(
            ['address', 'uint256', 'address', 'uint16'],
            [HONEY_TOKEN, amount_in_wei, address, 18]
        )
        
        # Create data field
        data = method_id + params.hex()
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = {
            'from': address,
            'to': LENDING_CONTRACT,
            'value': 0,
            'gas': GAS_LIMIT,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'data': data
        }
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Supplying {amount_in_honey} HONEY (raw method)...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Supply successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Supply error: {str(e)}")
        return False

# Test execution
if __name__ == "__main__":
    print("Testing HONEY supply functionality...")
    try:
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            wallet_index = 0
            address = wallet_manager.get_address(wallet_index)
            print(f"Testing with wallet {wallet_index + 1} ({address})")
            
            # Test supply with random amount
            supply_honey(wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")
