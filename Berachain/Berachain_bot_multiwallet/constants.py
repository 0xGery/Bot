# Contract addresses
BGT_CONTRACT = "0xbDa130737BDd9618301681329bF2e46A016ff9Ad"
VALIDATOR_ADDRESS = "0x40495A781095932e2FC8dccA69F5e358711Fdd41"
HONEY_WBERA_VAULT = "0xAD57d7d39a487C04a44D3522b910421888Fb9C6d"

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

# Claim ABI
CLAIM_ABI = [{
    "inputs": [{"type": "address", "name": "game"}],
    "name": "getReward",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]
