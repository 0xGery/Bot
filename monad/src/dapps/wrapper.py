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
    CHAIN_ID, GAS_PRICE, WRAPPER_GAS,
    WMON
)

class Wrapper(BaseDapp):
    # WMON ABI
    WRAPPER_ABI = [
        {
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "src",
                    "type": "address"
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "guy",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "Approval",
            "type": "event"
        },
        {
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "dst",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "Deposit",
            "type": "event"
        },
        {
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "src",
                    "type": "address"
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "dst",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "Transfer",
            "type": "event"
        },
        {
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "src",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "Withdrawal",
            "type": "event"
        },
        {
            "stateMutability": "payable",
            "type": "fallback"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "name": "allowance",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "guy",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "approve",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "",
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
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [
                {
                    "internalType": "uint8",
                    "name": "",
                    "type": "uint8"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "dst",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "transfer",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "src",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "dst",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "transferFrom",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "wad",
                    "type": "uint256"
                }
            ],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    async def get_contract_addresses(self) -> Dict[str, str]:
        """Get Wrapper contract addresses"""
        return {
            'wmon': WMON,  # WMON contract on Monad testnet
        }

    async def get_wrapped_balance(self) -> int:
        """Get WMON balance of the current account"""
        addresses = await self.get_contract_addresses()
        wrapper = self._get_contract(addresses['wmon'], self.WRAPPER_ABI)
        
        balance = wrapper.functions.balanceOf(self.account.address).call()
        return balance

    async def wrap(self, amount: int) -> Dict:
        """
        Wrap native MON to WMON
        
        Args:
            amount: Amount of MON to wrap (in wei)
        """
        addresses = await self.get_contract_addresses()
        wrapper = self._get_contract(addresses['wmon'], self.WRAPPER_ABI)

        # Build wrap (deposit) transaction
        wrap_tx = wrapper.functions.deposit().build_transaction({
            'from': self.account.address,
            'value': amount,  # Amount of MON to wrap
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': WRAPPER_GAS,
            'gasPrice': GAS_PRICE,
            'chainId': CHAIN_ID
        })

        return await self._build_and_send_transaction(wrap_tx)

    async def unwrap(self, amount: int) -> Dict:
        """
        Unwrap WMON back to native MON
        
        Args:
            amount: Amount of WMON to unwrap (in wei)
        """
        addresses = await self.get_contract_addresses()
        wrapper = self._get_contract(addresses['wmon'], self.WRAPPER_ABI)

        # Build unwrap (withdraw) transaction
        unwrap_tx = wrapper.functions.withdraw(amount).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': WRAPPER_GAS,
            'gasPrice': GAS_PRICE,
            'chainId': CHAIN_ID
        })

        return await self._build_and_send_transaction(unwrap_tx)

    async def get_allowance(self, spender: str) -> int:
        """Get WMON allowance for a spender"""
        addresses = await self.get_contract_addresses()
        wrapper = self._get_contract(addresses['wmon'], self.WRAPPER_ABI)
        
        return await wrapper.functions.allowance(
            self.account.address,
            spender
        ).call() 