from utils import wallet_manager, check_connection, random_delay
from functions.lending import supply_honey
from functions.wrap import wrap_and_unwrap_bera
from functions.honey import mint_honey
from functions.claim import claim_bgt
from functions.delegate import (
    delegate_bgt, 
    activate_boost, 
    bgt_tracker, 
    BGT_CONTRACT, 
    BGT_ABI, 
    VALIDATOR_ADDRESS
)
from config import w3, rotate_rpc
import random
import time
import argparse
from datetime import datetime, timedelta
import threading
import queue

class MultiWalletScheduler:
    def __init__(self):
        self.wallet_states = {}
        self.running = True
        self.threads = []
        # Initialize state for each wallet
        for i in range(wallet_manager.total_wallets()):
            self.wallet_states[i] = {
                'last_mint_time': None,
                'last_bgt_claim_time': None,
                'last_boost_check_time': None,
                'mint_count': 0,
                'wrap_count': 0,
                'bgt_claim_count': 0,
                'bgt_delegate_count': 0,
                'bgt_claimed': False
            }
    
    def should_claim_bgt(self, wallet_index):
        """Check if it's time to claim BGT"""
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # If never claimed or last claim was more than 24 hours ago
        if (state['last_bgt_claim_time'] is None or 
            current_time - state['last_bgt_claim_time'] > timedelta(hours=24)):
            return True
        return False

    def should_mint_honey(self, wallet_index):
        """Check if it's time to mint HONEY"""
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # If never minted or last mint was more than 12 hours ago
        if (state['last_mint_time'] is None or 
            current_time - state['last_mint_time'] > timedelta(hours=12)):
            return True
        return False

    def should_delegate_bgt(self, wallet_index):
        """Check if we should delegate BGT"""
        state = self.wallet_states[wallet_index]
        wallet_data = bgt_tracker.wallet_data.get(str(wallet_index), {})
        
        current_time = datetime.now()
        last_claim_time = datetime.fromisoformat(wallet_data.get('last_claim_time', '2000-01-01T00:00:00')) if wallet_data.get('last_claim_time') else None
        last_delegation_time = datetime.fromisoformat(wallet_data.get('last_delegation_time', '2000-01-01T00:00:00')) if wallet_data.get('last_delegation_time') else None
        
        # Get current BGT balance and pending amount
        current_balance = wallet_data.get('last_known_balance', 0)
        pending_amount = wallet_data.get('pending_amount', 0)
        total_delegated = wallet_data.get('total_delegated', 0)
        
        # Calculate undelegated balance (total balance minus what's already delegated)
        undelegated_balance = current_balance - total_delegated
        
        # Delegate if:
        # 1. We have any undelegated balance OR pending amount AND
        # 2. Either:
        #    a. First time delegation (never delegated before) OR
        #    b. We just claimed (within last 30 seconds) OR
        #    c. It's been 12 hours since last delegation
        has_undelegated_funds = (undelegated_balance > 0) or (pending_amount > 0)
        first_time = wallet_data.get('first_delegation', True)
        just_claimed = last_claim_time and (current_time - last_claim_time).total_seconds() <= 30
        twelve_hours_passed = last_delegation_time and (current_time - last_delegation_time) > timedelta(hours=12)
        
        should_delegate = has_undelegated_funds and (first_time or just_claimed or twelve_hours_passed)
        
        if should_delegate:
            print(f"\n💎 BGT Delegation Check:")
            print(f"└─ Undelegated Balance: {w3.from_wei(undelegated_balance, 'ether')} BGT")
            print(f"└─ Pending Amount: {w3.from_wei(pending_amount, 'ether')} BGT")
            
        return should_delegate

    def should_activate_boost(self, wallet_index):
        try:
            address = wallet_manager.get_address(wallet_index)
            contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
            current_block = w3.eth.block_number
            
            # Get queued amount at current block
            queued_amount = contract.functions.queuedBoost(
                address,
                current_block
            ).call()
            
            if queued_amount == 0:
                print("\n📊 No queued balance to activate")
                return False
                
            # Get queue block from tracker
            wallet_data = bgt_tracker.wallet_data[str(wallet_index)]
            queued_boosts = wallet_data.get('queued_boosts', {})
            
            if not queued_boosts:
                return False
                
            # Check oldest queued boost
            oldest_queue_block = min(int(block) for block in queued_boosts.keys())
            blocks_passed = current_block - oldest_queue_block
            
            # Required blocks: 8186 + 5 blocks buffer
            REQUIRED_BLOCKS = 8186 + 5
            
            can_activate = blocks_passed >= REQUIRED_BLOCKS
            
            print(f"\n🔍 Boost Activation Check for Wallet {wallet_index + 1}:")
            print(f"├─ Address: {address}")
            print(f"├─ Queued Amount: {w3.from_wei(queued_amount, 'ether')} BGT")
            print(f"├─ Queue Block: {oldest_queue_block}")
            print(f"├─ Current Block: {current_block}")
            print(f"├─ Blocks Passed: {blocks_passed}/{REQUIRED_BLOCKS}")
            print(f"└─ Can Activate: {'✅' if can_activate else '❌'}")
            
            return can_activate
            
        except Exception as e:
            print(f"❌ Error checking boost activation: {str(e)}")
            if rotate_rpc():
                print("🔄 Retrying with new RPC...")
                return self.should_activate_boost(wallet_index)
            return False

    def execute_bgt_claim(self, wallet_index):
        """Execute BGT claim"""
        if claim_bgt(wallet_index):
            state = self.wallet_states[wallet_index]
            state['last_bgt_claim_time'] = datetime.now()
            state['bgt_claim_count'] += 1
            state['bgt_claimed'] = True

    def execute_mint_and_supply(self, wallet_index):
        """Execute HONEY mint and supply"""
        if mint_honey(1000000, wallet_index):  # 1 STGUSDC
            random_delay(5, 10)
            if supply_honey(1, wallet_index):  # Supply the minted HONEY
                state = self.wallet_states[wallet_index]
                state['last_mint_time'] = datetime.now()
                state['mint_count'] += 1

    def execute_wrap_unwrap(self, wallet_index):
        """Execute wrap and unwrap"""
        if wrap_and_unwrap_bera(wallet_index):  # No amount needed now
            state = self.wallet_states[wallet_index]
            state['wrap_count'] += 1

    def execute_bgt_delegate(self, wallet_index):
        """Execute BGT delegation"""
        if delegate_bgt(wallet_index):
            state = self.wallet_states[wallet_index]
            state['bgt_delegate_count'] += 1

    def execute_boost_activation(self, wallet_index):
        """Execute boost activation"""
        if activate_boost(wallet_index):
            state = self.wallet_states[wallet_index]
            state['last_boost_check_time'] = datetime.now()
    
    def execute_for_wallet(self, wallet_index):
        """Execute operations for a specific wallet"""
        try:
            address = wallet_manager.get_address(wallet_index)
            print(f"\n{'='*50}")
            print(f"🔄 Processing Wallet {wallet_index + 1}: {address}")
            print(f"{'='*50}\n")
            
            # Initialize wallet state if needed
            if wallet_index not in self.wallet_states:
                self.wallet_states[wallet_index] = {
                    'last_mint_time': None,
                    'last_bgt_claim_time': None,
                    'last_boost_check_time': None,
                    'mint_count': 0,
                    'wrap_count': 0,
                    'bgt_claim_count': 0,
                    'bgt_delegate_count': 0,
                    'bgt_claimed': False
                }
            
            state = self.wallet_states[wallet_index]
            
            # Check if it's time to claim BGT
            if self.should_claim_bgt(wallet_index):
                print("\n📥 CLAIMING BGT:")
                print("-"*30)
                self.execute_bgt_claim(wallet_index)
                random_delay(5, 10)
            
            # Check if it's time to mint and supply
            if self.should_mint_honey(wallet_index):
                print("\n🍯 MINTING & SUPPLYING HONEY:")
                print("-"*30)
                self.execute_mint_and_supply(wallet_index)
                random_delay(5, 10)
            
            # Always do wrap-unwrap
            print("\n💫 WRAP & UNWRAP BERA:")
            print("-"*30)
            self.execute_wrap_unwrap(wallet_index)
            random_delay(5, 10)
            
            # Check if we should delegate BGT
            if self.should_delegate_bgt(wallet_index):
                print("\n📊 DELEGATING BGT:")
                print("-"*30)
                self.execute_bgt_delegate(wallet_index)
                random_delay(5, 10)
            
            # Check if we should activate any boosts
            if self.should_activate_boost(wallet_index):
                print("\n🚀 ACTIVATING BOOST:")
                print("-"*30)
                self.execute_boost_activation(wallet_index)
                
        except Exception as e:
            print(f"\n❌ Error processing wallet {wallet_index + 1}: {str(e)}")

    def wallet_loop(self, wallet_index):
        """Continuous loop for a single wallet"""
        base_delay = random.uniform(10, 15)
        print("\n" + "="*50)
        print(f"🚀 Starting Wallet {wallet_index + 1}")
        print(f"⏱️  Base delay: {base_delay:.2f} seconds")
        print("="*50)
        
        while self.running:
            try:
                self.execute_for_wallet(wallet_index)
                delay = base_delay * random.uniform(0.8, 1.2)
                print(f"\n⏳ Wallet {wallet_index + 1} waiting {delay:.2f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"\n❌ Error in wallet {wallet_index + 1} loop: {str(e)}")
                time.sleep(random.uniform(10, 15))

    def start_all_wallets(self):
        """Start threads for all wallets"""
        for wallet_index in range(wallet_manager.total_wallets()):
            thread = threading.Thread(
                target=self.wallet_loop,
                args=(wallet_index,),
                name=f"Wallet-{wallet_index + 1}"
            )
            self.threads.append(thread)
            thread.start()
            time.sleep(2)  # Reduced from 2 seconds to 1 second

    def stop_all_wallets(self):
        """Stop all wallet threads gracefully"""
        print("\n" + "="*50)
        print("🛑 STOPPING ALL WALLETS")
        print("="*50)
        self.running = False
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
        
        # Print final statistics
        print("\n" + "="*50)
        print("📊 FINAL STATISTICS")
        print("="*50)
        for i in range(wallet_manager.total_wallets()):
            state = self.wallet_states[i]
            address = wallet_manager.get_address(i)
            print(f"\n🔹 Wallet {i+1} ({address}):")
            print(f"   ├─ 💫 Wrap-Unwrap cycles: {state['wrap_count']}")
            print(f"   ├─ 🍯 Mint-Supply cycles: {state['mint_count']}")
            print(f"   ├─ 📥 BGT Claims: {state['bgt_claim_count']}")
            print(f"   └─ 📊 BGT Delegations: {state['bgt_delegate_count']}")

def parse_args():
    parser = argparse.ArgumentParser(description='Multi-wallet BGT delegation bot')
    parser.add_argument(
        '--reset',
        choices=['all', 'queued', 'none'],
        default='queued',
        help='Reset mode: all (full reset), queued (only queued boosts), none (keep all data)'
    )
    return parser.parse_args()

def reset_all_data():
    """Reset all BGT tracker data"""
    bgt_tracker.wallet_data = {}
    bgt_tracker._save_data()
    print("✅ All BGT tracker data reset")

def clean_queued_boosts():
    """Clean only queued boosts data while keeping other stats"""
    for wallet_id in bgt_tracker.wallet_data:
        if 'queued_boosts' in bgt_tracker.wallet_data[wallet_id]:
            bgt_tracker.wallet_data[wallet_id]['queued_boosts'] = {}
    bgt_tracker._save_data()
    print("✅ Queued boosts data cleaned")

def main():
    if not check_connection():
        print("Failed to connect to network")
        return

    scheduler = MultiWalletScheduler()
    
    print("Starting multi-wallet transaction bot...")
    print(f"Total wallets: {wallet_manager.total_wallets()}")
    
    try:
        scheduler.start_all_wallets()
        
        # Keep main thread alive until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        scheduler.stop_all_wallets()

if __name__ == "__main__":
    args = parse_args()
    
    # Handle data reset based on command line argument
    if args.reset == 'all':
        reset_all_data()
    elif args.reset == 'queued':
        clean_queued_boosts()
    else:
        print("ℹ️ Keeping existing data")
    
    main()

