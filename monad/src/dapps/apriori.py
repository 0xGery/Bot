from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CHAIN_ID, GAS_PRICE, APRIORI_STAKE_GAS,
    APRMON, APRIORI_STAKING
)

class Apriori(BaseDapp):
    # Apriori Staking ABI
    STAKING_ABI = [
        {
            "inputs": [
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"}
            ],
            "name": "deposit",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function",
            "funcSelector": "0x6e553f65"
        },
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Apriori contract addresses"""
        return {
            'staking': APRIORI_STAKING,  # Apriori staking contract
            'aprmon': APRMON,           # aprMON token (same as staking)
        }

    async def get_aprmon_balance(self) -> int:
        """Get aprMON balance of the current account"""
        addresses = await self.get_contract_addresses()
        staking = self._get_contract(addresses['staking'], self.STAKING_ABI)
        
        balance = staking.functions.balanceOf(self.account.address).call()
        return balance

    async def stake(self, amount: int) -> Dict:
        """
        Stake MON to receive aprMON
        
        Args:
            amount: Amount of MON to stake (in wei)
        """
        try:
            addresses = await self.get_contract_addresses()
            staking = self._get_contract(addresses['staking'], self.STAKING_ABI)
            
            # Check MON balance first
            balance = self.web3.eth.get_balance(self.account.address)
            logger.info(f"Current MON balance: {Web3.from_wei(balance, 'ether'):.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient MON balance. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(amount, 'ether')}")

            # Build stake transaction with exact parameters from successful tx
            data = staking.encodeABI(
                fn_name='deposit',
                args=[amount, self.account.address]
            )

            # Build transaction with exact format from successful tx
            stake_tx = {
                'chainId': CHAIN_ID,
                'data': data,
                'from': self.account.address,
                'gas': hex(APRIORI_STAKE_GAS),  # Convert to hex
                'gasPrice': hex(GAS_PRICE),     # Convert to hex
                'nonce': hex(self.web3.eth.get_transaction_count(self.account.address)),
                'to': addresses['staking'],
                'value': hex(amount)  # Convert to hex
            }

            # Log transaction details for debugging
            logger.info(f"Sending deposit transaction: amount={Web3.from_wei(amount, 'ether'):.6f} MON, gas={APRIORI_STAKE_GAS}")
            
            receipt = await self._build_and_send_transaction(stake_tx)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Deposit failed: {str(e)}")
            # Re-raise to handle in the automation
            raise
