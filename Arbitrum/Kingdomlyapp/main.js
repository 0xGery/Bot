const ethers = require('ethers');
const readline = require('readline');
require('dotenv').config();

// Constants
const GAS_LIMIT = 284000;

// RPC endpoints list   
const RPC_ENDPOINTS = [
    'https://arbitrum.drpc.org',           // 73ms
    'https://arbitrum.blockpi.network/v1/rpc/public', // 78ms
    'https://rpc.ankr.com/arbitrum',       // 144ms
    'https://arb1.arbitrum.io/rpc',        // 347ms
    'https://arbitrum.llamarpc.com',       // 523ms
    'https://1rpc.io/arb'                  // 619ms
];

// ABI
const ABI = [
    "function batchMint(uint256 amount, uint256 mintId) payable returns (uint256)",
    "function mintLive() view returns (bool)",
    "function threeDollarsEth() view returns (uint256)",
    "function activeMintGroups(uint256) view returns (uint256)",
    "function contractPresaleActive(uint256) view returns (bool)"
];

// Function to get user input
async function getUserInput() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const question = (query) => new Promise((resolve) => rl.question(query, resolve));

    console.log("\n=== Precision Mint Bot Configuration ===");
    const contractAddress = await question("Enter contract address: ");
    
    console.log("\nMint Stage Options:");
    console.log("0. Stage 0");
    console.log("1. Stage 1");
    console.log("2. Stage 2");
    const mintStage = await question("Choose mint stage (0, 1, or 2): ");
    
    console.log("\nMint Time Setup Options:");
    console.log("1. UTC Time");
    console.log("2. Block Number");
    const timeOption = await question("Choose option (1 or 2): ");

    let targetTime;
    let targetBlock;

    if (timeOption === "1") {
        const utcTime = await question("Enter UTC time (format: YYYY-MM-DD HH:mm:ss): ");
        targetTime = new Date(utcTime);
    } else {
        targetBlock = await question("Enter target block number: ");
    }

    rl.close();
    return { contractAddress, mintStage, timeOption, targetTime, targetBlock };
}

class PrecisionMintBot {
    constructor(privateKey, walletId, contractAddress, mintStage) {
        this.currentProviderIndex = 0;
        // Create separate provider instances for different operations
        this.mintProviders = RPC_ENDPOINTS.map(endpoint => new ethers.JsonRpcProvider(endpoint));
        this.monitorProviders = RPC_ENDPOINTS.map(endpoint => new ethers.JsonRpcProvider(endpoint));
        this.wallet = new ethers.Wallet(privateKey);
        this.walletId = walletId;
        this.contractAddress = contractAddress;
        this.mintStage = mintStage;
        this.mintAttempted = false;
        this.fastestProvider = null;
    }

    async getFastestProvider(providers = this.monitorProviders) {
        const results = await Promise.allSettled(
            providers.map(async (provider, index) => {
                const start = Date.now();
                try {
                    await provider.getBlockNumber();
                    return { provider, latency: Date.now() - start, index };
                } catch {
                    return { latency: Infinity, index };
                }
            })
        );

        const fastest = results
            .filter(r => r.status === 'fulfilled' && r.value.latency !== Infinity)
            .sort((a, b) => a.value.latency - b.value.latency)[0];

        if (!fastest) throw new Error("No responsive providers");
        
        this.currentProviderIndex = fastest.value.index;
        return fastest.value.provider;
    }

    async getWorkingProvider(providers = this.monitorProviders) {
        const startIndex = this.currentProviderIndex;
        
        for (let i = 0; i < providers.length; i++) {
            try {
                const provider = providers[this.currentProviderIndex];
                await provider.getBlockNumber();
                return provider;
            } catch {
                this.currentProviderIndex = (this.currentProviderIndex + 1) % providers.length;
                if (this.currentProviderIndex === startIndex) {
                    await new Promise(r => setTimeout(r, 10)); 
                }
            }
        }
        throw new Error("No working providers");
    }

    async waitForMintTime(targetTime, targetBlock) {
        if (targetTime) {
            const now = new Date();
            const timeUntilMint = targetTime - now;
            
            if (timeUntilMint > 200) { // 200ms buffer
                await new Promise(r => setTimeout(r, timeUntilMint - 200));
            }
            
            // Waiting for last 200ms
            while (new Date() < targetTime) {
                const remaining = targetTime - new Date();
                if (remaining > 50) {
                    await new Promise(r => setTimeout(r, 10));
                } else if (remaining > 10) {
                    await new Promise(r => setTimeout(r, 2));
                } else {
                    await new Promise(r => setTimeout(r, 1));
                }
            }
        } else {
            // Block monitoring
            let lastBlock = 0;
            while (true) {
                try {
                    const provider = await this.getWorkingProvider();
                    const currentBlock = await provider.getBlockNumber();
                    
                    if (currentBlock >= targetBlock) break;
                    
                    if (currentBlock > lastBlock) {
                        console.log(`Wallet ${this.walletId} - Block ${currentBlock}/${targetBlock}`);
                        lastBlock = currentBlock;
                    }

                    if (currentBlock >= targetBlock - 1) {
                        await new Promise(r => setTimeout(r, 1));
                    } else {
                        await new Promise(r => setTimeout(r, 10));
                    }
                } catch {
                    continue; // try next provider
                }
            }
        }
    }

    async mint() {
        if (this.mintAttempted) return false;
        
        // Pre-prepare multiple providers for instant fallback
        const preparedProviders = await Promise.all(
            this.mintProviders.map(async provider => {
                try {
                    await provider.getBlockNumber();
                    return provider;
                } catch {
                    return null;
                }
            })
        );

        const workingProviders = preparedProviders.filter(p => p !== null);
        
        for (let attempt = 0; attempt < workingProviders.length; attempt++) {
            try {
                const provider = workingProviders[attempt];
                const contract = new ethers.Contract(this.contractAddress, ABI, this.wallet.connect(provider));
                
                // Parallel execution of pre-mint checks
                const [nonce, latestMintCost] = await Promise.all([
                    provider.getTransactionCount(this.wallet.address),
                    contract.threeDollarsEth()
                ]);

                const tx = await contract.batchMint(
                    1,
                    Number(this.mintStage),
                    {
                        value: latestMintCost,
                        gasLimit: GAS_LIMIT,
                        nonce,
                        maxFeePerGas: ethers.parseUnits("0.0135", "gwei"),
                        maxPriorityFeePerGas: ethers.parseUnits("0", "gwei"),
                        type: 2
                    }
                );

                console.log(`Wallet ${this.walletId} - Mint TX sent! Hash: ${tx.hash}`);
                this.mintAttempted = true;
                
                // Fire and forget confirmation
                tx.wait().then(receipt => {
                    console.log(`Wallet ${this.walletId} - Mint confirmed in block ${receipt.blockNumber}`);
                }).catch(() => {});
                
                return true;
            } catch (error) {
                if (attempt < workingProviders.length - 1) continue;
                console.log(`Wallet ${this.walletId} - All mint attempts failed`);
            }
        }
        return false;
    }

    async monitorWithPrecision(targetTime, targetBlock) {
        console.log(`Wallet ${this.walletId} - Starting monitoring with address: ${this.wallet.address}`);
        await this.waitForMintTime(targetTime, targetBlock);
        console.log(`Wallet ${this.walletId} - MINT TIME REACHED! Executing...`);
        await this.mint();
    }
}

async function main() {
    const { contractAddress, mintStage, timeOption, targetTime, targetBlock } = await getUserInput();

    // Create bot instances with mint stage
    const bots = [
        new PrecisionMintBot(process.env.PRIVATE_KEY_1, "1", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_2, "2", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_3, "3", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_4, "4", contractAddress, mintStage),
        new PrecisionMintBot(process.env.PRIVATE_KEY_5, "5", contractAddress, mintStage)
    ];

    // Display configuration
    console.log("\n=== Mint Configuration ===");
    console.log(`Contract Address: ${contractAddress}`);
    console.log(`Mint Stage: ${mintStage}`);
    if (targetTime) {
        console.log(`Target UTC Time: ${targetTime.toUTCString()}`);
        const timeUntilMint = targetTime - new Date();
        console.log(`Time until mint: ${(timeUntilMint / 1000).toFixed(2)} seconds`);
    } else {
        console.log(`Target Block: ${targetBlock}`);
    }
    console.log("\nStarting precision mint monitoring...");

    // Start bots with minimal delays
    await Promise.all(
        bots.map((bot, index) => 
            new Promise(r => setTimeout(r, index * 10)) // Reduced from 20ms to 10ms
                .then(() => bot.monitorWithPrecision(targetTime, targetBlock))
        )
    );
}

main().catch(console.error);
