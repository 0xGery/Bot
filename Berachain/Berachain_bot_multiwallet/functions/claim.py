import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode
from functions.delegate import bgt_tracker, BGT_ABI

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

def get_bgt_balance(wallet_index=0, retry_count=0):
    """Get BGT balance for the wallet"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return None
        
    try:
        address = wallet_manager.get_address(wallet_index)
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        balance_wei = bgt_contract.functions.balanceOf(address).call()
        balance_bgt = w3.from_wei(balance_wei, 'ether')
        print(f"Current BGT balance: {balance_bgt} BGT")
        return balance_wei
    except Exception as e:
        print(f"Error checking BGT balance: {str(e)}")
        if rotate_rpc():
            return get_bgt_balance(wallet_index, retry_count + 1)
        return None

def claim_bgt(wallet_index=0, retry_count=0):
    """Claim BGT rewards"""
    MAX_RETRIES = 3
    
    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached. Aborting operation.")
        return False
        
    try:
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        
        print("\n📥 CLAIMING BGT:")
        print("-"*30)
        print(f"Wallet {wallet_index + 1}: {address}")
        
        # Get BGT balance before claim
        print("\n💰 Pre-claim check:")
        balance_before = get_bgt_balance(wallet_index)
        if balance_before is None:
            return False
            
        bgt_tracker.update_balance(wallet_index, balance_before)
        
        contract = w3.eth.contract(address=HONEY_WBERA_VAULT, abi=CLAIM_ABI)
        
        transaction = contract.functions.getReward(
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
        print(f"\n🔄 Claiming BGT from HONEY-WBERA Vault...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Claim successful! Gas used: {receipt['gasUsed']}")
        
        # Get BGT balance after claim
        print("\n💰 Post-claim check:")
        balance_after = get_bgt_balance(wallet_index)
        if balance_after is None:
            return False
        
        # Calculate and track claimed amount
        claimed_amount = balance_after - balance_before
        if claimed_amount > 0:
            print(f"\n🎉 Claimed {w3.from_wei(claimed_amount, 'ether')} BGT")
            bgt_tracker.add_claim(claimed_amount, wallet_index)
            return True
        else:
            print("\nℹ️  No BGT claimed this time")
            return False
            
    except Exception as e:
        print(f"❌ Claim BGT error: {str(e)}")
        if rotate_rpc():
            return claim_bgt(wallet_index, retry_count + 1)
        return False

# Test execution
if __name__ == "__main__":
    print("Testing BGT claim functionality...")
    try:
        if w3.is_connected():
            print(f"✅ Connected to Berachain")
            print(f"📦 Current block: {w3.eth.block_number}")
            
            # Test with multiple wallets
            for i in range(wallet_manager.total_wallets()):
                print(f"\n🔄 Testing Wallet {i + 1}")
                address = wallet_manager.get_address(i)
                print(f"📍 Address: {address}")
                
                # Test claim for each wallet
                claim_bgt(i)
                random_delay(5, 10)  # Add delay between wallets
                
        else:
            print("❌ Failed to connect to Berachain")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
