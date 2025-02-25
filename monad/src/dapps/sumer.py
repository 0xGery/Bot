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
    CHAIN_ID, GAS_PRICE, APPROVAL_GAS, SUMER_DEPOSIT_GAS, SUMER_WITHDRAW_GAS,
    USDC, SUMER_LENDING, DEFAULT_REFERRAL_CODE, ERC20_ABI
)

class Sumer(BaseDapp):
    # Sumer Lending ABI
    LENDING_ABI = [
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                }
            ],
            "name": "mint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                }
            ],
            "name": "redeem",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "account",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Sumer contract addresses"""
        return {
            'lending': SUMER_LENDING,  # Sumer lending contract
            'usdc': USDC,             # USDC token
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

            await self._build_and_send_transaction(approve_tx)
            logger.info(f"Approved USDC spending for Sumer lending")

    async def get_sdr_balance(self) -> int:
        """Get sdrUSDC balance of the current account"""
        addresses = await self.get_contract_addresses()
        lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
        
        balance = lending.functions.balanceOf(self.account.address).call()
        return balance

    async def deposit(self, amount: int) -> Dict:
        """
        Deposit USDC into Sumer lending by minting sdrUSDC
        
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
            await self._ensure_token_approval(addresses['usdc'], addresses['lending'], amount)
            
            # Double check allowance after approval
            allowance = usdc.functions.allowance(self.account.address, addresses['lending']).call()
            logger.info(f"Current USDC allowance for Sumer: {allowance/1000000:.6f}")

            # Build mint transaction with exact parameters from successful tx
            mint_tx = lending.functions.mint(
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': SUMER_DEPOSIT_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending mint transaction: amount={amount/1000000:.6f} USDC, gas={mint_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(mint_tx)
            
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
        Redeem sdrUSDC to get back USDC
        
        Args:
            amount: Amount of sdrUSDC to redeem (in wei). If None, redeems entire balance.
        """
        try:
            addresses = await self.get_contract_addresses()
            lending = self._get_contract(addresses['lending'], self.LENDING_ABI)
            
            # If no amount specified, get full balance
            if amount is None:
                amount = await self.get_sdr_balance()
                
            if amount == 0:
                raise Exception("No sdrUSDC balance to redeem")
                
            logger.info(f"Current sdrUSDC balance: {amount/1000000:.6f}")

            # Build redeem transaction
            redeem_tx = lending.functions.redeem(
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': SUMER_WITHDRAW_GAS,
                'gasPrice': GAS_PRICE,
                'value': 0,
                'chainId': CHAIN_ID
            })

            # Log transaction details for debugging
            logger.info(f"Sending redeem transaction: amount={amount/1000000:.6f} sdrUSDC, gas={redeem_tx['gas']}")
            
            receipt = await self._build_and_send_transaction(redeem_tx)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise Exception(f"Transaction failed. Gas used: {receipt['gasUsed']}")
                
            return receipt
            
        except Exception as e:
            logger.error(f"Redeem failed: {str(e)}")
            # Re-raise to handle in the automation
            raise





