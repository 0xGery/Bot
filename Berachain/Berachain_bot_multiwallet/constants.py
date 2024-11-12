##########################################
# CONTRACT ADDRESSES
##########################################
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad" # BGT TOKEN CONTRACT
VALIDATOR_ADDRESS = "0x40495A781095932e2FC8dccA69F5e358711Fdd41" # VALIDATOR ADDRESS
HONEY_WBERA_VAULT = "0xAD57d7d39a487C04a44D3522b910421888Fb9C6d" # HONEY WBERA VAULT
WBERA_CONTRACT = "0x7507c1dc16935B82698e4C63f2746A2fCf994dF8" # WBERA TOKEN CONTRACT
LENDING_CONTRACT = "0x30A3039675E5b5cbEA49d9a5eacbc11f9199B86D" # LENDING CONTRACT
HONEY_TOKEN = "0x0E4aaF1351de4c0264C5c7056Ef3777b41BD8e03" # HONEY TOKEN CONTRACT
HONEY_MINT_CONTRACT = "0xAd1782b2a7020631249031618fB1Bd09CD926b31" # HONEY MINT CONTRACT
STGUSDC_CONTRACT = "0xd6D83aF58a19Cd14eF3CF6fe848C9A4d21e5727c" # STGUSDC TOKEN CONTRACT


##########################################
# CHAIN SETTINGS
########################################## 
CHAIN_ID = 80084
GAS_LIMIT = 300000

##########################################
# ABI
##########################################

# BGT Contract ABI
BGT_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "queuedBoost",
        "outputs": [{"type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "unboostedBalanceOf",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "validator", "type": "address"}
        ],
        "name": "boosted",
        "outputs": [{"type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "validator", "type": "address"}
        ],
        "name": "boostedQueue",
        "outputs": [
            {"name": "blockNumberLast", "type": "uint32"},
            {"name": "balance", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "validator", "type": "address"},
            {"name": "amount", "type": "uint128"}
        ],
        "name": "queueBoost",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "validator", "type": "address"}
        ],
        "name": "activateBoost",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Claim BGT ABI
CLAIM_ABI = [{
    "inputs": [{"type": "address", "name": "game"}],
    "name": "getReward",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# Lending ABI
LENDING_ABI = [{
    "inputs": [
        {"type": "address", "name": "asset"},
        {"type": "uint256", "name": "amount"},
        {"type": "address", "name": "onBehalfOf"},
        {"type": "uint16", "name": "referralCode"}
    ],
    "name": "supply",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# ERC20 ABI FOR APPROVALS
ERC20_ABI = [{
    "constant": True,
    "inputs": [{"name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "type": "function"
}, {
    "constant": False,
    "inputs": [
        {"name": "spender", "type": "address"},
        {"name": "amount", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}, {
    "constant": True,
    "inputs": [
        {"name": "owner", "type": "address"},
        {"name": "spender", "type": "address"}
    ],
    "name": "allowance",
    "outputs": [{"name": "", "type": "uint256"}],
    "type": "function"
}]


# Honey ABI
HONEY_ABI = [{
    "inputs": [
        {"type": "address", "name": "asset"},
        {"type": "uint256", "name": "amount"},
        {"type": "address", "name": "receiver"}
    ],
    "name": "mint",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# WBERA ABI
WBERA_ABI = [
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"type": "uint256", "name": "amount"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {   
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]
