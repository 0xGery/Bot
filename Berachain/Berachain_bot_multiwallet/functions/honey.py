import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3
from utils import wallet_manager, random_delay
from eth_abi import encode

# Contract addresses
HONEY_MINT_CONTRACT = "0xAd1782b2a7020631249031618fB1Bd09CD926b31"
STGUSDC_CONTRACT = "0xd6D83aF58a19Cd14eF3CF6fe848C9A4d21e5727c"

# ABI for HONEY minting
HONEY_ABI = [{
    "inputs": [
        {"type": "address", "name": "asset"},
        {"type": "uint256", "name": "amount"},
        {"type": "address", "name": "receiver"}
    ],
    "name": "mint",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# ABI for checking STGUSDC balance and approval
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

def check_and_approve_stgusdc(amount, wallet_index=0):
    """Check STGUSDC balance and approve if needed"""
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        stgusdc_contract = w3.eth.contract(address=STGUSDC_CONTRACT, abi=ERC20_ABI)
        
        # Check balance
        balance = stgusdc_contract.functions.balanceOf(address).call()
        print(f"STGUSDC Balance: {balance}")
        
        if balance < amount:
            print(f"Insufficient STGUSDC balance. Have {balance}, need {amount}")
            return False
            
        # Check current allowance
        allowance = stgusdc_contract.functions.allowance(address, HONEY_MINT_CONTRACT).call()
        if allowance < amount:
            print("Approving STGUSDC...")
            
            approve_txn = stgusdc_contract.functions.approve(
                HONEY_MINT_CONTRACT,
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

def mint_honey(amount=1000000, wallet_index=0):
    """Mint HONEY tokens from STGUSDC"""
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        if not check_and_approve_stgusdc(amount, wallet_index):
            return False
            
        contract = w3.eth.contract(address=HONEY_MINT_CONTRACT, abi=HONEY_ABI)
        
        transaction = contract.functions.mint(
            STGUSDC_CONTRACT,
            amount,
            address
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Minting HONEY...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Mint successful! Gas used: {receipt['gasUsed']}")
        
        return True
        
    except Exception as e:
        print(f"Mint error: {str(e)}")
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
            
            # Test mint with 1 STGUSDC (1000000 units considering decimals)
            mint_honey(1000000, wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")