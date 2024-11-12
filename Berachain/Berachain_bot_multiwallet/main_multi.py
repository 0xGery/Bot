from utils import wallet_manager, check_connection, random_delay
from functions.claim import claim_bgt
from functions.delegate import delegate_bgt, activate_boost, should_activate_boost
from functions.honey import mint_honey
from functions.lending import supply_honey
from functions.wrap import wrap_and_unwrap_bera, WBERA_CONTRACT, WBERA_ABI
from bgt_tracker import bgt_tracker
from constants import BGT_CONTRACT, VALIDATOR_ADDRESS, BGT_ABI
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
        
        # Add debug logging for wallet initialization
        total_wallets = wallet_manager.total_wallets()
        print(f"\n📊 Initializing {total_wallets} wallets")
        
        # Initialize state for each wallet
        for i in range(total_wallets):
            address = wallet_manager.get_address(i)
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
            print(f"✅ Initialized Wallet {i+1}: {address}")
    
    def should_claim_bgt(self, wallet_index):
        """Check if it's time to claim BGT"""
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # If never claimed or last claim was more than 24 hours ago
        if (state['last_bgt_claim_time'] is None or 
            current_time - state['last_bgt_claim_time'] > timedelta(hours=6)):
            return True
        return False

    def should_mint_honey(self, wallet_index):
        """Check if it's time to mint HONEY"""
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # If never minted or last mint was more than 12 hours ago
        if (state['last_mint_time'] is None or 
            current_time - state['last_mint_time'] > timedelta(minutes=random.randint(30, 50))):
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
        
        # Calculate undelegated balance
        undelegated_balance = current_balance - total_delegated
        
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
        """Check if any boosts are ready for activation"""
        from functions.delegate import should_activate_boost as check_boost_activation
        
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # Check every 30 minutes
        if (state['last_boost_check_time'] is None or 
            current_time - state['last_boost_check_time'] > timedelta(minutes=30)):
            state['last_boost_check_time'] = current_time
            # Use the actual block-based check from delegate.py
            return check_boost_activation(wallet_index)
        return False

    def execute_bgt_claim(self, wallet_index):
        """Execute BGT claim operation"""
        state = self.wallet_states[wallet_index]
        if claim_bgt(wallet_index):
            state['last_bgt_claim_time'] = datetime.now()
            state['bgt_claim_count'] += 1
            state['bgt_claimed'] = True

    def execute_bgt_delegate(self, wallet_index):
        """Execute BGT delegation operation"""
        state = self.wallet_states[wallet_index]
        if delegate_bgt(wallet_index):
            state['bgt_delegate_count'] += 1

    def execute_boost_activation(self, wallet_index):
        """Execute boost activation check"""
        activate_boost(wallet_index)

    def execute_mint_and_supply(self, wallet_index):
        """Execute HONEY mint and supply operations"""
        state = self.wallet_states[wallet_index]
        
        if mint_honey(wallet_index):
            state['last_mint_time'] = datetime.now()
            state['mint_count'] += 1
            random_delay(5, 10)
            
            # Try to supply after successful mint
            supply_honey(wallet_index)

    def execute_wrap_unwrap(self, wallet_index):
        """Execute wrap/unwrap operations"""
        state = self.wallet_states[wallet_index]
        if wrap_and_unwrap_bera(wallet_index):
            state['wrap_count'] += 1

    def execute_wallet_operations(self, wallet_index):
        """Execute operations for a specific wallet"""
        try:
            address = wallet_manager.get_address(wallet_index)
            print(f"\n==================================================")
            print(f"🔄 Processing Wallet {wallet_index + 1}: {address}")
            print(f"==================================================")
            
            # ACTIVE OPERATIONS
            # 1. BGT Claim Check
            if self.should_claim_bgt(wallet_index):
                print("\n📥 CLAIMING BGT:")
                print("-"*30)
                self.execute_bgt_claim(wallet_index)
                random_delay(5, 10)
                
            # 2. BGT Delegation Check
            if self.should_delegate_bgt(wallet_index):
                print("\n📊 DELEGATING BGT:")
                print("-"*30)
                self.execute_bgt_delegate(wallet_index)
                random_delay(5, 10)
                
            # 3. Boost Activation Check
            if self.should_activate_boost(wallet_index):
                print("\n🚀 ACTIVATING BOOST:")
                print("-"*30)
                self.execute_boost_activation(wallet_index)
                random_delay(5, 10)
            
            # 4. HONEY Mint & Supply Check
            if self.should_mint_honey(wallet_index):
                print("\n🍯 MINTING & SUPPLYING HONEY:")
                print("-"*30)
                self.execute_mint_and_supply(wallet_index)
                random_delay(5, 10)
                
            # 5. Wrap/Unwrap Check
            print("\n💫 WRAP & UNWRAP BERA:")
            print("-"*30)
            self.execute_wrap_unwrap(wallet_index)
            random_delay(5, 10)
            
        except Exception as e:
            print(f"❌ Error executing wallet operations: {str(e)}")

    def wallet_thread(self, wallet_index):
        """Thread function for each wallet"""
        address = wallet_manager.get_address(wallet_index)
        base_delay = random.uniform(10, 15)
        print(f"\n==================================================")
        print(f"🚀 Starting Wallet {wallet_index + 1}")
        print(f"⏱️  Base delay: {base_delay:.2f} seconds")
        print(f"==================================================")
        
        while self.running:
            try:
                print(f"\n🔄 Wallet-{wallet_index + 1} executing wallet operations")
                self.execute_wallet_operations(wallet_index)
                
                # Random delay between operations
                delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error in wallet thread {wallet_index + 1}: {str(e)}")
                time.sleep(5)  # Short delay on error

    def start_wallet(self, wallet_index):
        """Start operations for a single wallet"""
        thread_name = f"Wallet-{wallet_index + 1}"
        thread = threading.Thread(
            target=self.wallet_thread,
            args=(wallet_index,),
            name=thread_name,
            daemon=True
        )
        self.threads.append(thread)
        thread.start()
        print(f"\n🧵 {thread_name} started")
        return thread

    def start_all_wallets(self):
        """Start all wallet threads"""
        print("\n🚀 Starting {wallet_manager.total_wallets()} wallet threads")
        for i in range(wallet_manager.total_wallets()):
            thread = self.start_wallet(i)
            print(f"✅ Thread started for Wallet {i + 1}")

    def stop_all_wallets(self):
        """Stop all wallet threads"""
        print("\n==================================================")
        print("🛑 STOPPING ALL WALLETS")
        print("==================================================")
        self.running = False
        for thread in self.threads:
            thread.join()

    def check_thread_status(self):
        """Check and report status of all threads"""
        print("\n==================================================")
        print("🧵 THREAD STATUS")
        print("==================================================")
        for thread in self.threads:
            print(f"Thread {thread.name}: {'Active' if thread.is_alive() else 'Stopped'}")

def parse_args():
    parser = argparse.ArgumentParser(description='Multi-wallet transaction bot')
    parser.add_argument(
        '--reset',
        choices=['all', 'queued', 'none'],
        default='queued',
        help='Reset mode: all (full reset), queued (only queued boosts), none (keep all data)'
    )
    return parser.parse_args()

def reset_all_data():
    """Reset all wallet data"""
    print("\n🔄 RESETTING ALL DATA")
    print("="*50)
    
    # First show current status
    print("\n📊 CURRENT STATUS:")
    print("-"*30)
    for wallet_index in range(wallet_manager.total_wallets()):
        address = wallet_manager.get_address(wallet_index)
        print(f"\n🔍 Wallet {wallet_index + 1}: {address}")
        
        # Get BERA balance
        bera_balance = w3.eth.get_balance(address)
        print(f"├─ BERA: {w3.from_wei(bera_balance, 'ether')} BERA")
        
        # Get WBERA balance
        contract = w3.eth.contract(address=WBERA_CONTRACT, abi=WBERA_ABI)
        wbera_balance = contract.functions.balanceOf(address).call()
        print(f"├─ WBERA: {w3.from_wei(wbera_balance, 'ether')} WBERA")
        
        # Get BGT status
        bgt_contract = w3.eth.contract(address=BGT_CONTRACT, abi=BGT_ABI)
        total_balance = bgt_contract.functions.balanceOf(address).call()
        unboosted_balance = bgt_contract.functions.unboostedBalanceOf(address).call()
        queued_boost = bgt_contract.functions.queuedBoost(address).call()
        boosted_amount = bgt_contract.functions.boosted(address, VALIDATOR_ADDRESS).call()
        print(f"├─ Total BGT: {w3.from_wei(total_balance, 'ether')} BGT")
        print(f"├─ Unboosted BGT: {w3.from_wei(unboosted_balance, 'ether')} BGT")
        print(f"├─ Queued BGT: {w3.from_wei(queued_boost, 'ether')} BGT")
        print(f"└─ Boosted BGT: {w3.from_wei(boosted_amount, 'ether')} BGT")
    
    # Reset the tracker data
    bgt_tracker.wallet_data = {}
    bgt_tracker._save_data()
    print("\n✅ All data has been reset!")

def clean_queued_boosts():
    """Clean only queued boosts data while keeping other stats"""
    for wallet_id in bgt_tracker.wallet_data:
        if 'queued_boosts' in bgt_tracker.wallet_data[wallet_id]:
            bgt_tracker.wallet_data[wallet_id]['queued_boosts'] = {}
    bgt_tracker._save_data()
    print("✅ Queued boosts data cleaned")

if __name__ == "__main__":
    args = parse_args()
    if args.reset:
        reset_all_data()
        
    scheduler = MultiWalletScheduler()
    
    try:
        scheduler.start_all_wallets()
        
        # Add periodic thread status check
        while True:
            time.sleep(60)  # Check every minute
            scheduler.check_thread_status()
            
    except KeyboardInterrupt:
        print("\n⚠️ Keyboard interrupt detected")
        scheduler.stop_all_wallets()
