import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import w3, rotate_rpc
from utils import wallet_manager, random_delay
from eth_abi import encode
from functions.claim import claim_bgt
from constants import BGT_CONTRACT, VALIDATOR_ADDRESS, BGT_ABI
from bgt_tracker import bgt_tracker

def check_boost_status(wallet_index=0):
    """Check boost status for the wallet"""
    try:
        address = wallet_manager.get_address(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        current_block = w3.eth.block_number
        
        # Get all relevant balances
        total_balance = contract.functions.balanceOf(address).call()
        unboosted_balance = contract.functions.unboostedBalanceOf(address).call()
        queued_boost = contract.functions.queuedBoost(address).call()
        boosted_amount = contract.functions.boosted(address, VALIDATOR_ADDRESS).call()
        
        # Get queue block if there's a queued amount
        queue_block = 0
        if queued_boost > 0:
            queue_info = contract.functions.boostedQueue(address, VALIDATOR_ADDRESS).call()
            queue_block = queue_info[0]
        
        print(f"\n🔍 Boost Status:")
        print(f"├─ Total Balance: {w3.from_wei(total_balance, 'ether')} BGT")
        print(f"├─ Already Boosted: {w3.from_wei(boosted_amount, 'ether')} BGT")
        print(f"├─ Queue Block: {queue_block}")
        print(f"└─ Queued Amount: {w3.from_wei(queued_boost, 'ether')} BGT")
        
        return {
            'total_balance': total_balance,
            'unboosted_balance': unboosted_balance,
            'queued_boost': queued_boost,
            'boosted_amount': boosted_amount,
            'queue_block': queue_block,
            'current_block': current_block
        }
        
    except Exception as e:
        print(f"Error checking boost status: {str(e)}")
        if rotate_rpc():
            return check_boost_status(wallet_index)
        return None

def should_queue_boost(wallet_index=0):
    """Check if we should queue a boost"""
    try:
        status = check_boost_status(wallet_index)
        if not status:
            return False, 0
            
        available_to_delegate = status['unboosted_balance']
        
        if available_to_delegate > 0:
            print(f"\n✅ Can queue {w3.from_wei(available_to_delegate, 'ether')} BGT")
            return True, available_to_delegate
            
        print("\n❌ No BGT available to queue")
        return False, 0
        
    except Exception as e:
        print(f"Error checking queue status: {str(e)}")
        return False, 0

def should_activate_boost(wallet_index=0):
    """Check if any boosts are ready for activation"""
    try:
        status = check_boost_status(wallet_index)
        if not status:
            return False
            
        if status['queued_boost'] == 0:
            print("\nℹ️ No boost in queue")
            return False
            
        blocks_passed = status['current_block'] - status['queue_block']
        REQUIRED_BLOCKS = 8191  # 8186 + 5
        
        can_activate = (blocks_passed >= REQUIRED_BLOCKS and 
                       status['queue_block'] > 0 and 
                       status['queued_boost'] > 0)
        
        if can_activate:
            print(f"\n✅ Boost ready for activation!")
            print(f"├─ Queued Amount: {w3.from_wei(status['queued_boost'], 'ether')} BGT")
            print(f"├─ Blocks Passed: {blocks_passed}")
            print(f"└─ Required Blocks: {REQUIRED_BLOCKS}")
        
        return can_activate
        
    except Exception as e:
        print(f"❌ Error checking boost activation: {str(e)}")
        if rotate_rpc():
            return should_activate_boost(wallet_index)
        return False

def delegate_bgt(wallet_index=0, retry_count=0):
    """Queue boost for BGT delegation"""
    try:
        # Initialize or get wallet data
        if str(wallet_index) not in bgt_tracker.wallet_data:
            bgt_tracker.wallet_data[str(wallet_index)] = {
                'total_claimed': 0,
                'pending_amount': 0,
                'total_delegated': 0,
                'last_known_balance': 0,
                'first_delegation': True,
                'queued_boosts': {},
                'last_delegation_time': None,
                'last_claim_time': None,
                'claim_amounts': [],
                'bgt_claim_count': 0,
                'bgt_claimed': False,
                'last_boost_check_time': None
            }
        
        wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
        address = wallet_manager.get_address(wallet_index)
        account = wallet_manager.get_account(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get current status
        status = check_boost_status(wallet_index)
        if not status:
            return False
            
        # Calculate available amount to delegate
        available_to_delegate = status['unboosted_balance']
        
        if available_to_delegate <= 0:
            print("❌ No BGT available to delegate")
            return False
            
        print(f"\n💎 Delegating BGT:")
        print(f"├─ Available: {w3.from_wei(available_to_delegate, 'ether')} BGT")
        print(f"├─ Pending: {w3.from_wei(available_to_delegate, 'ether')} BGT")
        
        # Queue the boost transaction
        transaction = contract.functions.queueBoost(
            VALIDATOR_ADDRESS,
            available_to_delegate
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })
        
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"\n🔄 Queueing boost...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            print("❌ Transaction failed")
            return False
            
        print(f"✅ Boost queued successfully! Gas used: {receipt['gasUsed']}")
        
        # Get the block number when boost was queued
        queue_block = receipt['blockNumber']
        print(f"📦 Queued at block: {queue_block}")
        
        # Update tracker data
        wallet_data['total_delegated'] += available_to_delegate
        wallet_data['pending_amount'] = 0
        wallet_data['first_delegation'] = False
        wallet_data['last_delegation_time'] = datetime.now().isoformat()
        
        # Add to queued boosts with block number
        wallet_data['queued_boosts'][str(queue_block)] = {
            'amount': available_to_delegate,
            'queue_block': queue_block,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save updated data
        bgt_tracker._save_data()
        
        print(f"\n📊 Delegation Summary:")
        print(f"├─ Amount Queued: {w3.from_wei(available_to_delegate, 'ether')} BGT")
        print(f"├─ Queue Block: {queue_block}")
        print(f"├─ Required Blocks: 8186 + 5")
        print(f"└─ Activation Available: Block {queue_block + 8191}")
        
        return True
        
    except Exception as e:
        print(f"❌ Delegate error: {str(e)}")
        if retry_count < 3 and rotate_rpc():
            print("🔄 Retrying with new RPC...")
            return delegate_bgt(wallet_index, retry_count + 1)
        print("❌ Max retries (3) reached. Aborting delegation.")
        return False

def activate_boost(wallet_index=0, retry_count=0):
    """Activate queued boost"""
    try:
        address = wallet_manager.get_address(wallet_index)
        account = wallet_manager.get_account(wallet_index)
        contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        
        # Get pre-activation status
        status = check_boost_status(wallet_index)
        if not status:
            return False
            
        # Build transaction
        transaction = contract.functions.activateBoost(
            VALIDATOR_ADDRESS
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80084
        })
        
        signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"\n🔄 Activating boost...")
        print(f"📝 Tx Hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            print("❌ Transaction failed")
            return False
            
        print(f"✅ Boost activated successfully! Gas used: {receipt['gasUsed']}")
        
        # Get post-activation status
        post_status = check_boost_status(wallet_index)
        if post_status:
            print("\n📈 CHANGES:")
            queued_change = float(w3.from_wei(status['queued_boost'] - post_status['queued_boost'], 'ether'))
            boosted_change = float(w3.from_wei(post_status['boosted_amount'] - status['boosted_amount'], 'ether'))
            print(f"├─ Queued BGT: {queued_change:+.6f} BGT")
            print(f"└─ Boosted BGT: {boosted_change:+.6f} BGT")
            
        return True
            
    except Exception as e:
        print(f"❌ Activation error: {str(e)}")
        if retry_count < 3 and rotate_rpc():
            print("🔄 Retrying with new RPC...")
            return activate_boost(wallet_index, retry_count + 1)
        print("❌ Max retries (3) reached. Aborting activation.")
        return False

# Test execution
if __name__ == "__main__":
    print("Testing BGT delegation functionality...")
    try:
        if w3 and w3.is_connected():
            print(f"✅ Connected to Berachain")
            print(f"📦 Current block: {w3.eth.block_number}")
            
            for wallet_index in range(wallet_manager.total_wallets()):
                print(f"\n🔄 Processing Wallet {wallet_index + 1}")
                
                # 1. Try to claim BGT first
                claim_bgt(wallet_index)
                
                # 2. Check if we can queue a boost
                should_queue, amount = should_queue_boost(wallet_index)
                if should_queue:
                    delegate_bgt(wallet_index)
                
                # 3. Check if we can activate any boosts
                if should_activate_boost(wallet_index):
                    activate_boost(wallet_index)
                    
                random_delay(5, 10)  # Add delay between wallets
                
        else:
            print("❌ Failed to connect to Berachain")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
