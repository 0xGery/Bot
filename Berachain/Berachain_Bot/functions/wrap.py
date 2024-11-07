import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3
from utils import account, address, random_delay
from eth_abi import encode
from web3 import Web3

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

def get_wbera_balance():
    """Get WBERA balance for the wallet"""
    try:
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        balance_wei = contract.functions.balanceOf(address).call()
        balance_bera = w3.from_wei(balance_wei, 'ether')
        print(f"Current WBERA balance: {balance_bera} WBERA")
        return balance_wei
    except Exception as e:
        print(f"Error checking WBERA balance: {str(e)}")
        return 0

def wrap_and_unwrap_bera(amount_in_bera=100):
    """
    Wraps and then unwraps specified amount of BERA
    Returns True if both transactions succeed
    """
    try:
        # Convert BERA amount to Wei
        amount_in_wei = w3.to_wei(amount_in_bera, 'ether')
        
        # Check both BERA and WBERA balances
        bera_balance = w3.eth.get_balance(address)
        wbera_balance = get_wbera_balance()
        
        print(f"Current balances:")
        print(f"BERA: {w3.from_wei(bera_balance, 'ether')} BERA")
        print(f"WBERA: {w3.from_wei(wbera_balance, 'ether')} WBERA")
        
        # If we have enough WBERA, just unwrap it
        if wbera_balance >= amount_in_wei:
            print(f"Found sufficient WBERA balance, unwrapping {amount_in_bera} WBERA...")
            return unwrap_bera(amount_in_wei)
            
        # If we have some WBERA but not enough, unwrap it first
        elif wbera_balance > 0:
            print(f"Found {w3.from_wei(wbera_balance, 'ether')} WBERA, unwrapping first...")
            unwrap_success = unwrap_bera(wbera_balance)
            if not unwrap_success:
                print("Failed to unwrap existing WBERA")
                return False
            random_delay(5, 15)
            # Refresh BERA balance after unwrap
            bera_balance = w3.eth.get_balance(address)
        
        # Check if we have enough BERA to wrap
        if bera_balance < (amount_in_wei + w3.to_wei(0.01, 'ether')):  # Add buffer for gas
            print(f"Insufficient BERA balance. Have {w3.from_wei(bera_balance, 'ether')}, need {amount_in_bera + 0.01}")
            return False
        
        # Proceed with wrap
        wrap_success = wrap_bera(amount_in_wei)
        if not wrap_success:
            print("Wrap failed")
            return False
            
        # Random delay between wrap and unwrap
        random_delay(5, 15)
        
        # Verify WBERA balance before unwrapping
        wbera_balance = get_wbera_balance()
        if wbera_balance < amount_in_wei:
            print(f"WBERA balance too low. Have {w3.from_wei(wbera_balance, 'ether')}, need {amount_in_bera}")
            return False
        
        # Then unwrap
        unwrap_success = unwrap_bera(amount_in_wei)
        
        return wrap_success and unwrap_success
        
    except Exception as e:
        print(f"Wrap and unwrap bundle error: {str(e)}")
        return False

def wrap_bera(amount_in_wei):
    try:
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = contract.functions.deposit().build_transaction({
            'from': address,
            'value': amount_in_wei,  # Amount of BERA to wrap
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Wrapping {w3.from_wei(amount_in_wei, 'ether')} BERA...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Wrap successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Wrap error: {str(e)}")
        return False

def unwrap_bera(amount_in_wei):
    try:
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = contract.functions.withdraw(amount_in_wei).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Unwrapping {w3.from_wei(amount_in_wei, 'ether')} BERA...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Unwrap successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Unwrap error: {str(e)}")
        return False

# Alternative raw method implementation if needed
def wrap_bera_raw(amount_in_wei):
    try:
        # Method ID for deposit()
        method_id = "0xd0e30db0"
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = {
            'from': address,
            'to': WBERA_CONTRACT,
            'value': amount_in_wei,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': 80084,
            'data': method_id
        }
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Wrapping {w3.from_wei(amount_in_wei, 'ether')} BERA (raw method)...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Wrap successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Wrap error: {str(e)}")
        return False

def unwrap_bera_raw(amount_in_wei):
    try:
        # Method ID for withdraw(uint256)
        method_id = "0x2e1a7d4d"
        
        # Encode amount parameter
        params = encode(['uint256'], [amount_in_wei])
        
        # Create data field
        data = method_id + params.hex()
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = {
            'from': address,
            'to': WBERA_CONTRACT,
            'value': 0,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': 80084,
            'data': data
        }
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Unwrapping {w3.from_wei(amount_in_wei, 'ether')} BERA (raw method)...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Unwrap successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Unwrap error: {str(e)}")
        return False

# Add this at the end of the file:
if __name__ == "__main__":
    print("Testing wrap and unwrap functionality...")
    try:
        # Check connection
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            print(f"Your wallet address: {address}")
            balance = w3.eth.get_balance(address)
            print(f"Wallet balance: {w3.from_wei(balance, 'ether')} BERA")
            
            # Test wrap and unwrap with 0.1 BERA
            wrap_and_unwrap_bera(100)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")