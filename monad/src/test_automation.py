# This code is to test a single dapp function to check if the dapps we are working on works or no

import asyncio
import sys
import random
from typing import Dict
from loguru import logger
from colorama import init, Fore, Style
from web3 import Web3

from config import Config
from dapps import Wrapper, Sumer, Nostra, Kinza, Curvance, Kintsu, Apriori, Magma
from settings import (
    MIN_BALANCE_MON,
    MIN_BALANCE_USDC,
    MIN_BALANCE_WBTC,
    USDC,
    WBTC,
    ERC20_ABI,
    MIN_LENDING_AMOUNT_USDC,
    MAX_LENDING_AMOUNT_USDC,
    MIN_LENDING_AMOUNT_WBTC,
    MAX_LENDING_AMOUNT_WBTC,
    MIN_STAKE_AMOUNT_MON,
    MAX_STAKE_AMOUNT_MON
)

# Initialize colorama
init(autoreset=True)

logger.remove()
logger.add(
    sys.stdout,
    format=f"{Fore.GREEN}{{time:YYYY-MM-DD HH:mm:ss}}{Style.RESET_ALL} | "
           f"{Fore.BLUE}{{level}}{Style.RESET_ALL} | "
           f"{Fore.CYAN}{{message}}{Style.RESET_ALL}"
)
logger.add("test_transactions.log", rotation="500 MB")

class TestAutomation:
    def __init__(self):
        self.config = Config()
        self.web3 = self.config.get_web3()
        self.wallets = self.config.get_wallets()
        
        # Initialize dapps
        self.dapps = {}
        self._initialize_dapps()

    def _initialize_dapps(self):
        """Initialize all supported dapps"""
        for wallet in self.wallets:
            self.dapps[wallet['address']] = {
                'wrapper': Wrapper(self.web3, wallet['account']),
                'sumer': Sumer(self.web3, wallet['account']),
                'nostra': Nostra(self.web3, wallet['account']),
                'kinza': Kinza(self.web3, wallet['account']),
                'curvance': Curvance(self.web3, wallet['account']),
                'kintsu': Kintsu(self.web3, wallet['account']),
                'apriori': Apriori(self.web3, wallet['account']),
                'magma': Magma(self.web3, wallet['account'])
            }

    async def check_wallet_balances(self):
        """Check if wallets have sufficient balances to operate"""
        for wallet in self.wallets:
            # Check MON balance
            mon_balance = self.web3.eth.get_balance(wallet['address'])
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} MON balance: {Web3.from_wei(mon_balance, 'ether'):.6f}{Style.RESET_ALL}")
            
            if mon_balance < MIN_BALANCE_MON:
                raise Exception(f"Wallet {wallet['address']} has insufficient MON: {Web3.from_wei(mon_balance, 'ether')}. Minimum required: 0.01 MON")

            # Check USDC balance
            usdc = self.web3.eth.contract(
                address=USDC,
                abi=ERC20_ABI
            )
            
            usdc_balance = usdc.functions.balanceOf(wallet['address']).call()
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} USDC balance: {usdc_balance/1000000:.6f}{Style.RESET_ALL}")
            
            if usdc_balance < MIN_BALANCE_USDC:
                raise Exception(f"Wallet {wallet['address']} has insufficient USDC: {usdc_balance/1000000:.6f}. Minimum required: 0.002 USDC")

            # Check WBTC balance
            wbtc = self.web3.eth.contract(
                address=WBTC,
                abi=ERC20_ABI
            )
            
            wbtc_balance = wbtc.functions.balanceOf(wallet['address']).call()
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} WBTC balance: {wbtc_balance/10**8:.8f}{Style.RESET_ALL}")
            
            if wbtc_balance < MIN_BALANCE_WBTC:
                raise Exception(f"Wallet {wallet['address']} has insufficient WBTC: {wbtc_balance/10**8:.8f}. Minimum required: 0.000001 WBTC")

    async def test_wrapper(self, wallet: Dict):
        """Test wrap/unwrap functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Wrapper for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['wrapper']
        amount = Web3.to_wei(0.001, 'ether')  # Fixed small amount for testing

        try:
            # Check native balance
            balance = self.web3.eth.get_balance(wallet['address'])
            if balance < amount:
                raise Exception(f"Insufficient MON balance. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(amount, 'ether')}")

            # Execute wrap
            receipt = await dapp.wrap(amount)
            logger.success(f"{Fore.GREEN}Successfully wrapped {Web3.from_wei(amount, 'ether')} MON to WMON{Style.RESET_ALL}")

            # Wait 5 seconds before unwrap
            await asyncio.sleep(5)
            logger.info("Waiting 5 seconds before unwrap...")

            # Get current WMON balance
            wmon_balance = await dapp.get_wrapped_balance()
            
            if wmon_balance > 0:
                # Unwrap entire WMON balance
                receipt = await dapp.unwrap(wmon_balance)
                logger.success(f"{Fore.GREEN}Successfully unwrapped {Web3.from_wei(wmon_balance, 'ether')} WMON to MON{Style.RESET_ALL}")
            else:
                logger.warning(f"{Fore.YELLOW}No WMON balance to unwrap{Style.RESET_ALL}")
                
            return True
        except Exception as e:
            logger.error(f"{Fore.RED}Wrapper test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_sumer(self, wallet: Dict):
        """Test Sumer deposit functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Sumer for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['sumer']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited {amount/1000000:.6f} USDC to Sumer{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Sumer deposit failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Sumer test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_nostra(self, wallet: Dict):
        """Test Nostra deposit functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Nostra for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['nostra']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited {amount/1000000:.6f} USDC to Nostra{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Nostra deposit failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Nostra test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_kinza(self, wallet: Dict):
        """Test Kinza deposit functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Kinza for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['kinza']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited {amount/1000000:.6f} USDC to Kinza{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Kinza deposit failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Kinza test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_curvance(self, wallet: Dict):
        """Test Curvance deposit functionality (randomly selects between WBTC and USDC)"""
        logger.info(f"{Fore.MAGENTA}Testing Curvance for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['curvance']

        try:
            # Execute deposit - amount will be randomly chosen in the deposit function
            receipt = await dapp.deposit()
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited to Curvance{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Curvance deposit failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Curvance test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_kintsu(self, wallet: Dict):
        """Test Kintsu staking functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Kintsu for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['kintsu']
        amount = Web3.to_wei(0.01, 'ether')  # Fixed amount of 0.01 MON

        try:
            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether'):.6f} MON on Kintsu{Style.RESET_ALL}")
                
                # Get sMON balance after staking
                smon_balance = await dapp.get_smon_balance()
                logger.info(f"{Fore.WHITE}Current sMON balance: {Web3.from_wei(smon_balance, 'ether'):.6f}{Style.RESET_ALL}")
                
                return True
            else:
                logger.error(f"{Fore.RED}Kintsu stake failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Kintsu test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_apriori(self, wallet: Dict):
        """Test Apriori staking functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Apriori for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['apriori']
        amount = Web3.to_wei(0.0001, 'ether')  # Fixed amount from successful tx: 0.0001 MON

        try:
            # Check MON balance first
            balance = self.web3.eth.get_balance(wallet['address'])
            logger.info(f"Current MON balance: {Web3.from_wei(balance, 'ether'):.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient MON balance. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(amount, 'ether')}")

            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether')} MON to Apriori{Style.RESET_ALL}")
                
                # Get current aprMON balance
                aprmon_balance = await dapp.get_aprmon_balance()
                if aprmon_balance > 0:
                    logger.success(f"{Fore.GREEN}Current aprMON balance: {Web3.from_wei(aprmon_balance, 'ether')}{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Apriori stake failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Apriori test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def test_magma(self, wallet: Dict):
        """Test Magma staking functionality"""
        logger.info(f"{Fore.MAGENTA}Testing Magma for wallet {wallet['address']}{Style.RESET_ALL}")
        dapp = self.dapps[wallet['address']]['magma']
        amount = Web3.to_wei(0.00001, 'ether')  # Fixed amount from successful tx: 0.00001 MON

        try:
            # Check MON balance first
            balance = self.web3.eth.get_balance(wallet['address'])
            logger.info(f"Current MON balance: {Web3.from_wei(balance, 'ether'):.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient MON balance. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(amount, 'ether')}")

            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether')} MON to Magma{Style.RESET_ALL}")
                
                # Get current gMON balance
                gmon_balance = await dapp.get_gmon_balance()
                if gmon_balance > 0:
                    logger.success(f"{Fore.GREEN}Current gMON balance: {Web3.from_wei(gmon_balance, 'ether')}{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}Magma stake failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            logger.error(f"{Fore.RED}Magma test failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def run_tests(self, test_type: str = None):
        """Run the automation process"""
        try:
            logger.info(f"{Fore.GREEN}Starting Dapp Testing{Style.RESET_ALL}")
            
            # Check wallet balances first
            await self.check_wallet_balances()
            
            # Execute tests based on type
            for wallet in self.wallets:
                logger.info(f"\n{Fore.WHITE}Testing wallet {wallet['address']}{Style.RESET_ALL}")
                
                if test_type == "wrapper":
                    success = await self.test_wrapper(wallet)
                elif test_type == "sumer":
                    success = await self.test_sumer(wallet)
                elif test_type == "nostra":
                    success = await self.test_nostra(wallet)
                elif test_type == "kinza":
                    success = await self.test_kinza(wallet)
                elif test_type == "curvance":
                    success = await self.test_curvance(wallet)
                elif test_type == "kintsu":
                    success = await self.test_kintsu(wallet)
                elif test_type == "apriori":
                    success = await self.test_apriori(wallet)
                elif test_type == "magma":
                    success = await self.test_magma(wallet)
                else:
                    # Run all tests in sequence
                    await self.test_wrapper(wallet)
                    await self.test_sumer(wallet)
                    await self.test_nostra(wallet)
                    await self.test_kinza(wallet)
                    await self.test_curvance(wallet)
                    await self.test_kintsu(wallet)
                    await self.test_apriori(wallet)
                    await self.test_magma(wallet)
            
            logger.success(f"{Fore.GREEN}Testing completed!{Style.RESET_ALL}")
            
        except Exception as e:
            logger.error(f"{Fore.RED}Testing failed: {str(e)}{Style.RESET_ALL}")
        finally:
            logger.info("Testing finished")

if __name__ == "__main__":
    # Get test type from command line argument
    test_type = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Validate test type
    valid_types = ["wrapper", "sumer", "nostra", "kinza", "curvance", "kintsu", "apriori", "magma"]
    if test_type and test_type not in valid_types:
        print(f"Invalid test type. Please use one of: {', '.join(valid_types)}")
        sys.exit(1)
    
    automation = TestAutomation()
    asyncio.run(automation.run_tests(test_type)) 