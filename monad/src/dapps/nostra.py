from typing import Dict
from decimal import Decimal
from .base import BaseDapp
from web3 import Web3
from loguru import logger
import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CHAIN_ID, GAS_PRICE, APPROVAL_GAS, NOSTRA_DEPOSIT_GAS, NOSTRA_WITHDRAW_GAS,
    USDC, NOSTRA_LENDING, DEFAULT_REFERRAL_CODE, ERC20_ABI
)

class Nostra(BaseDapp):
    # Nostra Lending ABI
    LENDING_ABI = [
        {
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"}
            ],
            "name": "deposit",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "receiver", "type": "address"},
                {"name": "value", "type": "uint256"}
            ],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "account", "type": "address"}
            ],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Nostra contract addresses"""
        return {
            'lending': NOSTRA_LENDING,  # Nostra lending contract
            'usdc': USDC,              # USDC token
        }

    async def _ensure_token_approval(self, token_address: str, spender: str, amount: int) -> None:
        """Ensure token approval for spender"""
        token_contract = self._get_contract(token_address, ERC20_ABI)
        
        # Check current allowance
        allowance = token_contract.functions.allowance(
            self.account.address,
            spender
        ).call()

        if allowance < amount:
            # Approve if needed
            approve_tx = token_contract.functions.approve(
                spender,
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': APPROVAL_GAS,
                'gasPrice': GAS_PRICE,
                'chainId': CHAIN_ID
            })

            receipt = await self._build_and_send_transaction(approve_tx)
            logger.info(f"Approved USDC spending for Nostra lending")
            return receipt

    async def get_iusdc_balance(self) -> int:
        """Get iUSDC balance of the current account"""
        addresses = await self.get_contract_addresses()
        lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
        
        balance = lending.functions.balanceOf(self.account.address).call()
        return balance

    async def deposit(self, amount: int) -> Dict:
        """
        Deposit USDC into Nostra lending by minting iUSDC
        
        Args:
            amount: Amount of USDC to deposit (in wei)
        """
        try:
            addresses = await self.get_contract_addresses()
            lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
            
            # Check USDC balance first
            usdc = self._get_contract(addresses['usdc'], ERC20_ABI)
            balance = usdc.functions.balanceOf(self.account.address).call()
            logger.info(f"Current USDC balance: {balance/1000000:.6f}")
            
            if balance < amount:
                raise Exception(f"Insufficient USDC balance. Have: {balance/1000000:.6f}, Need: {amount/1000000:.6f}")

            # First ensure USDC is approved
            approval_receipt = await self._ensure_token_approval(addresses['usdc'], addresses['lending'], amount)
            
            # If we got an approval receipt, we need to wait a bit before proceeding
            if approval_receipt:
                # Wait for a few seconds after approval
                await asyncio.sleep(5)
            
            # Double check allowance after approval
            allowance = usdc.functions.allowance(self.account.address, addresses['lending']).call()
            logger.info(f"Current USDC allowance for Nostra: {allowance/1000000:.6f}")

            # Build deposit transaction with exact parameters from successful tx
            deposit_tx = lending.functions.deposit(
                self.account.address,  # to
                amount               # value
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': NOSTRA_DEPOSIT_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending deposit transaction: amount={amount/1000000:.6f} USDC, gas={deposit_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(deposit_tx)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Deposit failed: {str(e)}")
            # Re-raise to handle in the automation
            raise

    async def withdraw(self, amount: int = None) -> Dict:
        """
        Withdraw USDC from Nostra lending by redeeming iUSDC
        
        Args:
            amount: Amount of iUSDC to withdraw (in wei). If None, withdraws entire balance.
        """
        try:
            addresses = await self.get_contract_addresses()
            lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
            
            # If no amount specified, get full balance
            if amount is None:
                amount = await self.get_iusdc_balance()
                
            if amount == 0:
                raise Exception("No iUSDC balance to withdraw")
                
            logger.info(f"Current iUSDC balance: {amount/1000000:.6f}")

            # Build withdraw transaction
            withdraw_tx = lending.functions.withdraw(
                self.account.address,  # to
                self.account.address,  # receiver (same as to)
                amount                # value
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': NOSTRA_WITHDRAW_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending withdraw transaction: amount={amount/1000000:.6f} iUSDC, gas={withdraw_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(withdraw_tx)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Withdraw failed: {str(e)}")
            # Re-raise to handle in the automation
            raise
