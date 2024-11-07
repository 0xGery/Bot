from utils import check_connection, random_delay
from functions.lending import supply_honey
from functions.wrap import wrap_and_unwrap_bera
from functions.honey import mint_honey
from functions.claim import claim_bgt
from functions.delegate import delegate_bgt, activate_boost
import random
import time
from datetime import datetime, timedelta

class TransactionScheduler:
    def __init__(self):
        self.last_mint_time = None
        self.last_bgt_claim_time = None
        self.last_boost_check_time = None
        self.mint_count = 0
        self.wrap_count = 0
        self.bgt_claim_count = 0
        self.bgt_delegate_count = 0
        self.WRAP_AMOUNT = 100  # Fixed wrap amount of 100 BERA
        self.bgt_claimed = False  # Flag to track if BGT was claimed
        
    def should_mint_honey(self):
        """Check if it's time to mint honey (every 30 minutes)"""
        if self.last_mint_time is None:
            return True
        time_since_last_mint = datetime.now() - self.last_mint_time
        return time_since_last_mint >= timedelta(minutes=30)
    
    def should_claim_bgt(self):
        """Check if it's time to claim BGT (every 24 hours)"""
        if self.last_bgt_claim_time is None:
            return True
        time_since_last_claim = datetime.now() - self.last_bgt_claim_time
        return time_since_last_claim >= timedelta(hours=24)
    
    def should_delegate_bgt(self):
        """Check if we should delegate BGT (after claim and some operations)"""
        return self.bgt_claimed and self.wrap_count % 5 == 0  # Every 5 wrap cycles after claim
    
    def execute_bgt_claim(self):
        """Execute BGT claim only"""
        try:
            print("\nExecuting BGT Claim...")
            self.bgt_claim_count += 1
            print(f"BGT Claim cycle #{self.bgt_claim_count}")
            
            # Claim BGT
            if claim_bgt():
                self.last_bgt_claim_time = datetime.now()
                self.bgt_claimed = True
                print("BGT claimed successfully, will delegate after some operations")
                return True
            
            return False
        except Exception as e:
            print(f"Error in BGT claim cycle: {str(e)}")
            return False

    def execute_bgt_delegate(self):
        """Execute BGT delegate only"""
        try:
            print("\nExecuting BGT Delegate...")
            self.bgt_delegate_count += 1
            print(f"BGT Delegate cycle #{self.bgt_delegate_count}")
            
            # Delegate BGT
            if delegate_bgt():
                self.last_bgt_delegate_time = datetime.now()
                self.bgt_claimed = False  # Reset the claim flag
                print("BGT delegated successfully")
                return True
            
            return False
        except Exception as e:
            print(f"Error in BGT delegate cycle: {str(e)}")
            return False

    def execute_wrap_unwrap(self):
        """Execute wrap and unwrap with fixed amount"""
        try:
            print("\nExecuting Wrap-Unwrap cycle...")
            self.wrap_count += 1
            print(f"Wrap-Unwrap cycle #{self.wrap_count}")
            
            # Use fixed amount of 100 BERA
            wrap_and_unwrap_bera(self.WRAP_AMOUNT)
            
            # Wait 10-15 seconds before next cycle
            delay = random.uniform(10, 15)
            print(f"Waiting {delay:.2f} seconds before next wrap-unwrap cycle...")
            time.sleep(delay)
            
            return True
        except Exception as e:
            print(f"Error in wrap-unwrap cycle: {str(e)}")
            return False

    def execute_mint_and_supply(self):
        """Execute mint honey and supply to lending"""
        try:
            print("\nExecuting Mint-Supply cycle...")
            self.mint_count += 1
            print(f"Mint-Supply cycle #{self.mint_count}/48")
            
            # Mint HONEY
            mint_success = mint_honey(1000000)  # Adjust amount as needed
            if mint_success:
                # Wait a bit before supplying
                time.sleep(random.uniform(5, 10))
                
                # Supply the minted HONEY to lending
                supply_success = supply_honey(1)  # Adjust amount as needed
                if supply_success:
                    self.last_mint_time = datetime.now()
                    return True
            
            return False
        except Exception as e:
            print(f"Error in mint-supply cycle: {str(e)}")
            return False

    def should_activate_boost(self):
        """Check if we should look for boosts to activate"""
        if self.last_boost_check_time is None:
            return True
        time_since_last_check = datetime.now() - self.last_boost_check_time
        return time_since_last_check >= timedelta(minutes=30)  # Check every 30 minutes
    
    def execute_boost_activation(self):
        """Execute boost activation if any are ready"""
        try:
            print("\nChecking for activatable boosts...")
            if activate_boost():
                self.last_boost_check_time = datetime.now()
                return True
            return False
        except Exception as e:
            print(f"Error in boost activation cycle: {str(e)}")
            return False

def main():
    if not check_connection():
        print("Failed to connect to network")
        return

    scheduler = TransactionScheduler()
    
    print("Starting transaction bot...")
    print(f"- Wrap-Unwrap: Every 10-15 seconds (Fixed amount: {scheduler.WRAP_AMOUNT} BERA)")
    print("- Mint-Supply: Every 30 minutes (48 times per day)")
    print("- BGT Claim: Every 24 hours")
    print("- BGT Delegate: After claim and 5 wrap-unwrap cycles")
    
    while True:
        try:
            # Check if it's time to claim BGT
            if scheduler.should_claim_bgt():
                scheduler.execute_bgt_claim()
            
            # Check if it's time to mint and supply
            if scheduler.should_mint_honey() and scheduler.mint_count < 48:
                scheduler.execute_mint_and_supply()
            
            # Always do wrap-unwrap
            scheduler.execute_wrap_unwrap()
            
            # Check if we should delegate BGT
            if scheduler.should_delegate_bgt():
                scheduler.execute_bgt_delegate()
                
            # Check if we should activate any boosts
            if scheduler.should_activate_boost():
                scheduler.execute_boost_activation()
                
        except KeyboardInterrupt:
            print("\nBot stopped by user")
            print(f"Statistics:")
            print(f"- Wrap-Unwrap cycles completed: {scheduler.wrap_count}")
            print(f"- Mint-Supply cycles completed: {scheduler.mint_count}")
            print(f"- BGT Claims completed: {scheduler.bgt_claim_count}")
            print(f"- BGT Delegations completed: {scheduler.bgt_delegate_count}")
            break
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(random.uniform(5, 20))

if __name__ == "__main__":
    main()