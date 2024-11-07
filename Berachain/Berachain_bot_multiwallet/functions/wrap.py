import sys
import os
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3
from utils import wallet_manager, random_delay
from eth_abi import encode

# Contract address
WBERA_CONTRACT = "0x7507c1dc16935B82698e4C63f2746A2fCf994dF8"

# ABI for WBERA contract
WBERA_ABI = [
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"type": "uint256", "name": "amount"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {   # Add balanceOf function
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

def get_wbera_balance(wallet_index=0):
    """Get WBERA balance for the wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        balance_wei = contract.functions.balanceOf(address).call()
        balance_bera = w3.from_wei(balance_wei, 'ether')
        print(f"Current WBERA balance: {balance_bera} WBERA")
        return balance_wei
    except Exception as e:
        print(f"Error checking WBERA balance: {str(e)}")
        return 0

def wrap_and_unwrap_bera(wallet_index=0):
    """Wrap random amount of BERA and unwrap all WBERA"""
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        # Random amount between 50-100 BERA
        amount_in_bera = random.uniform(50, 100)
        amount_in_wei = w3.to_wei(amount_in_bera, 'ether')
        
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        
        # Wrap BERA
        wrap_txn = contract.functions.deposit().build_transaction({
            'from': address,
            'value': amount_in_wei,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })
        
        signed_txn = w3.eth.account.sign_transaction(wrap_txn, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Wrapping {amount_in_bera:.4f} BERA...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Wrap successful! Gas used: {receipt['gasUsed']}")
        
        random_delay(5, 10)
        
        # Get total WBERA balance
        wbera_balance = get_wbera_balance(wallet_index)
        if wbera_balance == 0:
            print("No WBERA balance to unwrap")
            return False
            
        # Unwrap all WBERA
        unwrap_txn = contract.functions.withdraw(wbera_balance).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })
        
        signed_txn = w3.eth.account.sign_transaction(unwrap_txn, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Unwrapping {w3.from_wei(wbera_balance, 'ether')} WBERA...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Unwrap successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Wrap/Unwrap error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing wrap and unwrap functionality...")
    try:
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            wallet_index = 0
            address = wallet_manager.get_address(wallet_index)
            print(f"Testing with wallet {wallet_index + 1} ({address})")
            balance = w3.eth.get_balance(address)
            print(f"Wallet balance: {w3.from_wei(balance, 'ether')} BERA")
            
            # Test wrap and unwrap with 0.1 BERA
            wrap_and_unwrap_bera(wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")
