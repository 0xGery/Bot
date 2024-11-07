from config import w3
from utils import wallet_manager, random_delay
from eth_abi import encode
from .delegate import bgt_tracker, BGT_ABI

# Contract details
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"
HONEY_WBERA_VAULT = "0xAD57d7d39a487C04a44D3522b910421888Fb9C6d"

# ABI for the getReward function in the HONEY-WBERA Vault
CLAIM_ABI = [{
    "inputs": [{"type": "address", "name": "game"}],
    "name": "getReward",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

def get_bgt_balance(wallet_index=0):
    """Get BGT balance for the wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        balance_wei = bgt_contract.functions.balanceOf(address).call()
        balance_bgt = w3.from_wei(balance_wei, 'ether')
        print(f"Current BGT balance: {balance_bgt} BGT")
        return balance_wei
    except Exception as e:
        print(f"Error checking BGT balance: {str(e)}")
        return 0

def claim_bgt(wallet_index=0):
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        # Create contract instance
        vault_contract = w3.eth.contract(address=HONEY_WBERA_VAULT, abi=CLAIM_ABI)
        
        # Get BGT balance before claim
        balance_before = get_bgt_balance(wallet_index)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # Build transaction
        transaction = vault_contract.functions.getReward(
            address  # Now using wallet's own address
        ).build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })

        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Claiming BGT from HONEY-WBERA Vault...")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Claim successful! Gas used: {receipt['gasUsed']}")
        
        # Get BGT balance after claim
        balance_after = get_bgt_balance(wallet_index)
        
        # Calculate claimed amount
        claimed_amount = balance_after - balance_before
        print(f"Claimed {w3.from_wei(claimed_amount, 'ether')} BGT")
        
        # Update tracker
        bgt_tracker.add_claim(claimed_amount)
        
        return True
        
    except Exception as e:
        print(f"Claim BGT error: {str(e)}")
        return False

# Test execution
if __name__ == "__main__":
    print("Testing BGT claim functionality...")
    try:
        if w3.is_connected():
            print(f"Connected to Berachain")
            print(f"Current block number: {w3.eth.block_number}")
            wallet_index = 0
            address = wallet_manager.get_address(wallet_index)
            print(f"Testing with wallet {wallet_index + 1} ({address})")
            
            # Test claim
            claim_bgt(wallet_index)
        else:
            print("Failed to connect to Berachain")
    except Exception as e:
        print(f"Error: {str(e)}")