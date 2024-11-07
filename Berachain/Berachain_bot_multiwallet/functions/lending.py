import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3
from utils import wallet_manager, random_delay
from eth_abi import encode
from web3 import Web3

# Contract addresses
LENDING_CONTRACT = "0x30A3039675E5b5cbEA49d9a5eacbc11f9199B86D"
HONEY_TOKEN = "0x0E4aaF1351de4c0264C5c7056Ef3777b41BD8e03"

# ABI for lending and token contracts
LENDING_ABI = [{
    "inputs": [
        {"type": "address", "name": "asset"},
        {"type": "uint256", "name": "amount"},
        {"type": "address", "name": "onBehalfOf"},
        {"type": "uint16", "name": "referralCode"}
    ],
    "name": "supply",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

ERC20_ABI = [{
    "constant": True,
    "inputs": [{"name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "type": "function"
}, {
    "constant": False,
    "inputs": [
        {"name": "spender", "type": "address"},
        {"name": "amount", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}, {
    "constant": True,
    "inputs": [
        {"name": "owner", "type": "address"},
        {"name": "spender", "type": "address"}
    ],
    "name": "allowance",
    "outputs": [{"name": "", "type": "uint256"}],
    "type": "function"
}]

def check_and_approve_honey(amount, wallet_index=0):
    """Check HONEY balance and approve if needed"""
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        honey_contract = w3.eth.contract(address=HONEY_TOKEN, abi=ERC20_ABI)
        
        balance = honey_contract.functions.balanceOf(address).call()
        print(f"HONEY Balance: {w3.from_wei(balance, 'ether')} HONEY")
        
        if balance < amount:
            print(f"Insufficient HONEY balance")
            return False
            
        allowance = honey_contract.functions.allowance(address, LENDING_CONTRACT).call()
        if allowance < amount:
            print("Approving HONEY...")
            
            approve_txn = honey_contract.functions.approve(
                LENDING_CONTRACT,
                amount
            ).build_transaction({
                'from': address,
                'nonce': w3.eth.get_transaction_count(address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 80084
            })
            
            signed_txn = w3.eth.account.sign_transaction(approve_txn, account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Approval transaction hash: {tx_hash.hex()}")
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Approval successful! Gas used: {receipt['gasUsed']}")
            
            random_delay(5, 10)
            
        return True
        
    except Exception as e:
        print(f"Approval error: {str(e)}")
        return False

def supply_honey(amount_in_honey=1, wallet_index=0):
    """Supply HONEY to lending protocol"""
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        amount_in_wei = w3.to_wei(amount_in_honey, 'ether')
        
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
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Supplying {amount_in_honey} HONEY...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Supply successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Supply error: {str(e)}")
        return False

# Alternative raw method implementation
def supply_honey_raw(amount_in_honey=1, wallet_index=0):
    """Supply HONEY to lending protocol using raw transaction"""
    try:
        account = wallet_manager.get_account(wallet_index)  # Get account from wallet manager
        address = wallet_manager.get_address(wallet_index)  # Get address from wallet manager
        
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
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': 80084,
            'data': data
        }
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
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
            
            # Test supply with 1 HONEY
            supply_honey(1, wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")