from utils import wallet_manager, check_connection, random_delay
from functions.lending import supply_honey
from functions.wrap import wrap_and_unwrap_bera
from functions.honey import mint_honey
from functions.claim import claim_bgt
from functions.delegate import delegate_bgt, activate_boost
import random
import time
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
        return state['bgt_claimed'] and state['bgt_delegate_count'] < state['bgt_claim_count']

    def should_activate_boost(self, wallet_index):
        """Check if it's time to check for activatable boosts"""
        state = self.wallet_states[wallet_index]
        current_time = datetime.now()
        
        # Check every 6 hours
        if (state['last_boost_check_time'] is None or 
            current_time - state['last_boost_check_time'] > timedelta(hours=6)):
            return True
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
        account = wallet_manager.get_account(wallet_index)
        address = wallet_manager.get_address(wallet_index)
        state = self.wallet_states[wallet_index]
        
        print(f"\nProcessing Wallet {wallet_index + 1} ({address})")
        
        try:
            # Check if it's time to claim BGT
            if self.should_claim_bgt(wallet_index):
                self.execute_bgt_claim(wallet_index)
                random_delay(10, 20)
            
            # Check if it's time to mint and supply
            if self.should_mint_honey(wallet_index):
                self.execute_mint_and_supply(wallet_index)
                random_delay(10, 20)
            
            # Always do wrap-unwrap
            self.execute_wrap_unwrap(wallet_index)
            random_delay(10, 20)
            
            # Check if we should delegate BGT
            if self.should_delegate_bgt(wallet_index):
                self.execute_bgt_delegate(wallet_index)
                random_delay(10, 20)
            
            # Check if we should activate any boosts
            if self.should_activate_boost(wallet_index):
                self.execute_boost_activation(wallet_index)
                
        except Exception as e:
            print(f"Error processing wallet {wallet_index + 1}: {str(e)}")

    def wallet_loop(self, wallet_index):
        """Continuous loop for a single wallet"""
        base_delay = random.uniform(5, 10)  # Changed to 5-10 seconds
        print(f"Wallet {wallet_index + 1} starting with {base_delay:.2f} seconds base delay")
        
        while self.running:
            try:
                self.execute_for_wallet(wallet_index)
                
                # Random delay with some variation around the base delay
                delay = base_delay * random.uniform(0.8, 1.2)
                print(f"\nWallet {wallet_index + 1} waiting {delay:.2f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error in wallet {wallet_index + 1} loop: {str(e)}")
                time.sleep(random.uniform(5, 10))  # Also adjusted error delay

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
            # Small delay between starting threads to avoid rate limiting
            time.sleep(2)

    def stop_all_wallets(self):
        """Stop all wallet threads gracefully"""
        print("\nStopping all wallets...")
        self.running = False
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
        
        # Print final statistics
        for i in range(wallet_manager.total_wallets()):
            state = self.wallet_states[i]
            address = wallet_manager.get_address(i)
            print(f"\nWallet {i+1} ({address}) Statistics:")
            print(f"- Wrap-Unwrap cycles: {state['wrap_count']}")
            print(f"- Mint-Supply cycles: {state['mint_count']}")
            print(f"- BGT Claims: {state['bgt_claim_count']}")
            print(f"- BGT Delegations: {state['bgt_delegate_count']}")

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
    main()
