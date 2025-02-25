import asyncio
import random
from typing import List, Dict
from datetime import datetime
from loguru import logger
import sys
from colorama import init, Fore, Back, Style
from web3 import Web3

from src.config import Config
from src.dapps import Wrapper, Sumer, Nostra, Kinza, Curvance, Kintsu, Apriori, Magma
from src.settings import (
    SUMER_LENDING_AMOUNT,
    NOSTRA_LENDING_AMOUNT,
    MIN_BALANCE_MON,
    MIN_BALANCE_USDC,
    MIN_BALANCE_WBTC,
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
logger.add("transactions.log", rotation="500 MB")

class MonadAutomation:
    def __init__(self):
        self.config = Config()
        self.web3 = self.config.get_web3()
        self.wallets = self.config.get_wallets()
        self.initial_mon_balances = {}  # Store initial MON balances
        
        # Initialize dapps
        self.dapps = {}
        self._initialize_dapps()
        
        # Transaction settings
        self.dice_times = 100  # Number of random transactions to execute
        self.transaction_types = {
            1: "wrap_unwrap",
            2: "wrap_unwrap",
            3: "sumer_deposit_withdraw",
            4: "sumer_deposit_withdraw",
            5: "nostra_deposit_withdraw",
            6: "nostra_deposit_withdraw",
            7: "kinza_deposit",
            8: "kinza_deposit",
            9: "curvance_deposit",
            10: "curvance_deposit",
            11: "kintsu_stake",
            12: "kintsu_stake",
            13: "apriori_stake",
            14: "apriori_stake",
            15: "magma_stake",
            16: "magma_stake"
        }

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
        """Check if wallets have sufficient balances and store initial MON balances"""
        min_mon = Web3.to_wei(0.01, 'ether')  # Minimum 0.01 MON required
        min_usdc = 2000  # Minimum 0.002 USDC required
        
        for wallet in self.wallets:
            # Check and store MON balance
            mon_balance = self.web3.eth.get_balance(wallet['address'])
            self.initial_mon_balances[wallet['address']] = mon_balance
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} Initial MON balance: {Web3.from_wei(mon_balance, 'ether'):.6f}{Style.RESET_ALL}")
            
            if mon_balance < min_mon:
                raise Exception(f"Wallet {wallet['address']} has insufficient MON: {Web3.from_wei(mon_balance, 'ether')}. Minimum required: 0.01 MON")

            # Check USDC balance
            usdc = self.web3.eth.contract(
                address=Web3.to_checksum_address('0xf817257fed379853cDe0fa4F97AB987181B1E5Ea'),
                abi=[{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            )
            
            usdc_balance = usdc.functions.balanceOf(wallet['address']).call()
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} USDC balance: {usdc_balance/1000000:.6f}{Style.RESET_ALL}")
            
            if usdc_balance < min_usdc:
                raise Exception(f"Wallet {wallet['address']} has insufficient USDC: {usdc_balance/1000000:.6f}. Minimum required: 0.002 USDC")

            # Check WBTC balance
            wbtc = self.web3.eth.contract(
                address=Web3.to_checksum_address('0x6BB379A2056d1304E73012b99338F8F581eE2E18'),
                abi=[{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            )
            
            wbtc_balance = wbtc.functions.balanceOf(wallet['address']).call()
            logger.info(f"{Fore.WHITE}Wallet {wallet['address']} WBTC balance: {wbtc_balance/10**8:.8f}{Style.RESET_ALL}")
            
            if wbtc_balance < MIN_BALANCE_WBTC:
                raise Exception(f"Wallet {wallet['address']} has insufficient WBTC: {wbtc_balance/10**8:.8f}. Minimum required: 0.000001 WBTC")

    async def calculate_gas_fees(self):
        """Calculate total gas fees spent in MON"""
        total_fees = 0
        
        for wallet in self.wallets:
            final_balance = self.web3.eth.get_balance(wallet['address'])
            initial_balance = self.initial_mon_balances[wallet['address']]
            fees_spent = initial_balance - final_balance
            
            logger.info(
                f"\n{Fore.YELLOW}Wallet {wallet['address']} Gas Fee Summary:{Style.RESET_ALL}\n"
                f"Initial Balance: {Web3.from_wei(initial_balance, 'ether'):.6f} MON\n"
                f"Final Balance: {Web3.from_wei(final_balance, 'ether'):.6f} MON\n"
                f"Total Fees Spent: {Web3.from_wei(fees_spent, 'ether'):.6f} MON"
            )
            
            total_fees += fees_spent
            
        logger.info(
            f"\n{Fore.MAGENTA}Total Gas Fees Summary:{Style.RESET_ALL}\n"
            f"Total MON Spent on Gas: {Web3.from_wei(total_fees, 'ether'):.6f} MON"
        )
        
        return total_fees

    async def random_delay(self):
        delay = random.randint(self.config.min_delay, self.config.max_delay)
        
        # Initial message without newline
        print(f"\n{Fore.YELLOW}Waiting for {delay} seconds before next transaction{Style.RESET_ALL}", end='', flush=True)
        
        for remaining in range(delay, 0, -1):
            # Clear the current line and show updated countdown
            print(f"\r{Fore.YELLOW}Waiting for {remaining} seconds before next transaction{Style.RESET_ALL}", end='', flush=True)
            await asyncio.sleep(1)
        
        # Print newline after countdown finishes
        print("")

    async def execute_wrap_unwrap(self, wallet: Dict):
        """Execute wrap MON to WMON and then unwrap all WMON"""
        dapp = self.dapps[wallet['address']]['wrapper']
        amount = Web3.to_wei(random.uniform(0.001, 0.005), 'ether')  # Random amount between 0.001-0.005 MON

        try:
            # Check native balance
            balance = self.web3.eth.get_balance(wallet['address'])
            if balance < amount:
                logger.warning(f"{Fore.YELLOW}Insufficient MON balance for wrapping. Balance: {Web3.from_wei(balance, 'ether')} MON{Style.RESET_ALL}")
                return None

            # Execute wrap
            receipt = await dapp.wrap(amount)
            logger.success(f"{Fore.GREEN}Wrapped {Web3.from_wei(amount, 'ether')} MON to WMON{Style.RESET_ALL}")

            # Short random delay between wrap and unwrap (5-10 seconds)
            delay = random.randint(5, 10)
            
            # Initial message without newline
            print(f"\n{Fore.YELLOW}Waiting {delay} seconds before unwrapping{Style.RESET_ALL}", end='', flush=True)
            
            for remaining in range(delay, 0, -1):
                # Clear the current line and show updated countdown
                print(f"\r{Fore.YELLOW}Waiting {remaining} seconds before unwrapping{Style.RESET_ALL}", end='', flush=True)
                await asyncio.sleep(1)
            
            # Print newline after countdown finishes
            print("")

            # Get current WMON balance
            wmon_balance = await dapp.get_wrapped_balance()
            
            if wmon_balance > 0:
                # Unwrap entire WMON balance
                receipt = await dapp.unwrap(wmon_balance)
                logger.success(f"{Fore.GREEN}Unwrapped all WMON balance: {Web3.from_wei(wmon_balance, 'ether')} WMON to MON{Style.RESET_ALL}")
            else:
                logger.warning(f"{Fore.YELLOW}No WMON balance to unwrap{Style.RESET_ALL}")
                
            return receipt
        except Exception as e:
            logger.error(f"{Fore.RED}Wrap/Unwrap cycle failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_sumer_deposit_withdraw(self, wallet: Dict):
        """Execute USDC deposit to Sumer lending followed by withdrawal"""
        dapp = self.dapps[wallet['address']]['sumer']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit first
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully minted {amount/1000000:.6f} sdrUSDC from USDC deposit{Style.RESET_ALL}")
                
                # Short delay between deposit and withdrawal (5-10 seconds)
                delay = random.randint(5, 10)
                print(f"\n{Fore.YELLOW}Waiting {delay} seconds before withdrawal{Style.RESET_ALL}", end='', flush=True)
                for remaining in range(delay, 0, -1):
                    print(f"\r{Fore.YELLOW}Waiting {remaining} seconds before withdrawal{Style.RESET_ALL}", end='', flush=True)
                    await asyncio.sleep(1)
                print("")

                # Get current sdrUSDC balance
                balance = await dapp.get_sdr_balance()
                if balance > 0:
                    # Execute withdrawal
                    receipt = await dapp.withdraw()
                    if receipt and receipt.get('status') == 1:
                        logger.success(f"{Fore.GREEN}Successfully withdrew {balance/1000000:.6f} sdrUSDC from Sumer lending{Style.RESET_ALL}")
                else:
                    logger.warning(f"{Fore.YELLOW}No sdrUSDC balance to withdraw{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Deposit transaction failed. Please check transaction for details.{Style.RESET_ALL}")
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Sumer deposit/withdraw cycle failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_nostra_deposit_withdraw(self, wallet: Dict):
        """Execute USDC deposit to Nostra lending followed by withdrawal"""
        dapp = self.dapps[wallet['address']]['nostra']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit first
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited {amount/1000000:.6f} USDC to Nostra lending{Style.RESET_ALL}")
                
                # Short delay between deposit and withdrawal (5-10 seconds)
                delay = random.randint(5, 10)
                print(f"\n{Fore.YELLOW}Waiting {delay} seconds before withdrawal{Style.RESET_ALL}", end='', flush=True)
                for remaining in range(delay, 0, -1):
                    print(f"\r{Fore.YELLOW}Waiting {remaining} seconds before withdrawal{Style.RESET_ALL}", end='', flush=True)
                    await asyncio.sleep(1)
                print("")

                # Get current iUSDC balance
                balance = await dapp.get_iusdc_balance()
                if balance > 0:
                    # Execute withdrawal
                    receipt = await dapp.withdraw()
                    if receipt and receipt.get('status') == 1:
                        logger.success(f"{Fore.GREEN}Successfully withdrew {balance/1000000:.6f} iUSDC from Nostra lending{Style.RESET_ALL}")
                else:
                    logger.warning(f"{Fore.YELLOW}No iUSDC balance to withdraw{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Deposit transaction failed. Please check transaction for details.{Style.RESET_ALL}")
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Nostra deposit/withdraw cycle failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_curvance_deposit(self, wallet: Dict):
        """Execute deposit to Curvance lending (randomly selects between WBTC and USDC)"""
        dapp = self.dapps[wallet['address']]['curvance']

        try:
            # Execute deposit - amount and token will be randomly chosen in the deposit function
            receipt = await dapp.deposit()
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited to Curvance lending{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Curvance deposit failed{Style.RESET_ALL}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Curvance deposit failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_kinza_deposit(self, wallet: Dict):
        """Execute deposit to Kinza lending"""
        dapp = self.dapps[wallet['address']]['kinza']
        amount = random.randint(MIN_LENDING_AMOUNT_USDC, MAX_LENDING_AMOUNT_USDC)

        try:
            # Execute deposit
            receipt = await dapp.deposit(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully deposited {amount/1000000:.6f} USDC to Kinza lending{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Kinza deposit failed{Style.RESET_ALL}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Kinza deposit failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_kintsu_stake(self, wallet: Dict):
        """Execute MON staking on Kintsu"""
        dapp = self.dapps[wallet['address']]['kintsu']
        amount = random.randint(MIN_STAKE_AMOUNT_MON, MAX_STAKE_AMOUNT_MON)

        try:
            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether'):.6f} MON on Kintsu{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Kintsu stake failed{Style.RESET_ALL}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Kintsu stake failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_apriori_stake(self, wallet: Dict):
        """Execute MON staking on Apriori"""
        dapp = self.dapps[wallet['address']]['apriori']
        amount = Web3.to_wei(0.0001, 'ether')  # Fixed amount from successful tx: 0.0001 MON

        try:
            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether'):.6f} MON on Apriori{Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}Apriori stake failed{Style.RESET_ALL}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"{Fore.RED}Apriori stake failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_magma_stake(self, wallet: Dict):
        """Execute MON staking on Magma"""
        dapp = self.dapps[wallet['address']]['magma']
        amount = Web3.to_wei(0.00001, 'ether')  # Fixed amount from successful tx: 0.00001 MON

        try:
            # Execute stake
            receipt = await dapp.stake(amount)
            
            if receipt and receipt.get('status') == 1:
                logger.success(f"{Fore.GREEN}Successfully staked {Web3.from_wei(amount, 'ether'):.6f} MON on Magma{Style.RESET_ALL}")
                
                # Get gMON balance after staking
                gmon_balance = await dapp.get_gmon_balance()
                logger.info(f"{Fore.WHITE}Current gMON balance: {Web3.from_wei(gmon_balance, 'ether'):.6f}{Style.RESET_ALL}")
                
                return receipt
            else:
                logger.error(f"{Fore.RED}Magma stake failed{Style.RESET_ALL}")
                return None
                
        except Exception as e:
            logger.error(f"{Fore.RED}Magma stake failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def execute_random_transaction(self, wallet: Dict):
        """Execute a random transaction type"""
        roll = random.randint(1, 16)  # Updated to include Magma
        tx_type = self.transaction_types[roll]
        logger.info(f"{Fore.WHITE}Rolled {roll}, Selected transaction type: {tx_type}{Style.RESET_ALL}")

        if tx_type == "wrap_unwrap":
            return await self.execute_wrap_unwrap(wallet)
        elif tx_type == "sumer_deposit_withdraw":
            return await self.execute_sumer_deposit_withdraw(wallet)
        elif tx_type == "nostra_deposit_withdraw":
            return await self.execute_nostra_deposit_withdraw(wallet)
        elif tx_type == "kinza_deposit":
            return await self.execute_kinza_deposit(wallet)
        elif tx_type == "curvance_deposit":
            return await self.execute_curvance_deposit(wallet)
        elif tx_type == "kintsu_stake":
            return await self.execute_kintsu_stake(wallet)
        elif tx_type == "apriori_stake":
            return await self.execute_apriori_stake(wallet)
        else:  # magma_stake
            return await self.execute_magma_stake(wallet)

    async def run_automation(self):
        try:
            logger.info(f"{Fore.MAGENTA}Starting Random Pattern Automation{Style.RESET_ALL}")
            
            # Check wallet balances and store initial MON balances
            await self.check_wallet_balances()
            
            for wallet in self.wallets:
                logger.info(f"{Fore.WHITE}Processing wallet {wallet['address']}{Style.RESET_ALL}")
                
                # Execute random transactions
                for i in range(self.dice_times):
                    logger.info(f"{Fore.WHITE}Random Transaction {i + 1}/{self.dice_times}{Style.RESET_ALL}")
                    
                    # Execute random transaction
                    await self.execute_random_transaction(wallet)
                    
                    if i < self.dice_times - 1:
                        # Random delay between transactions
                        await self.random_delay()

            logger.success(f"{Fore.GREEN}Automation completed! All random transactions finished{Style.RESET_ALL}")
            
            # Calculate and display total gas fees spent
            await self.calculate_gas_fees()
            
        except Exception as e:
            logger.error(f"{Fore.RED}Automation error: {str(e)}{Style.RESET_ALL}")
        finally:
            logger.info(f"{Fore.MAGENTA}Automation finished{Style.RESET_ALL}")

async def main():
    automation = MonadAutomation()
    await automation.run_automation()

if __name__ == "__main__":
    logger.info(f"{Fore.MAGENTA}Starting Monad Random Pattern Automation{Style.RESET_ALL}")
    asyncio.run(main()) 