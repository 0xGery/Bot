# Monad Automation

An automated trading and interaction system for the Monad blockchain, supporting multiple DeFi protocols including Kintsu, Magma, and more.

## Features

-  Automated interactions with multiple DeFi protocols
-  Scheduled execution between 7 AM - 10 AM daily
-  Random pattern execution to simulate natural behavior
-  Multiple RPC support with automatic failover
-  Multi-wallet support
-  Secure environment variable configuration

## Supported Protocols

- Kintsu (Staking)
- Magma (gMON staking)
- Sumer
- Nostra
- Kinza
- Curvance
- Apriori

## Setup & Deployment

### Local Development

1. Clone the repository
```bash
git clone <repository-url>
cd monad-automation
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file from example
```bash
cp .env.example .env
```

5. Configure your environment variables in `.env`

### Zeabur Deployment

1. Push your code to a Git repository

2. In Zeabur dashboard:
   - Create a new project
   - Connect your repository
   - Set the following environment variables:
     ```
     WALLET_1_PRIVATE_KEY=your_private_key_here
     MONAD_RPC_URLS=https://testnet-rpc.monad.xyz,https://monad-testnet.drpc.org
     CHAIN_ID=10143
     MIN_DELAY_SECONDS=30
     MAX_DELAY_SECONDS=300
     MAX_RPC_TRIES=3
     RPC_TIMEOUT_SECONDS=10
     ```

3. Deploy your project

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONAD_RPC_URLS` | Comma-separated list of RPC URLs | https://testnet-rpc.monad.xyz,https://monad-testnet.drpc.org |
| `CHAIN_ID` | Monad chain ID | 10143 |
| `WALLET_1_PRIVATE_KEY` | Private key for wallet 1 | Required |
| `MIN_DELAY_SECONDS` | Minimum delay between transactions | 30 |
| `MAX_DELAY_SECONDS` | Maximum delay between transactions | 300 |
| `MAX_RPC_TRIES` | Maximum RPC retry attempts | 3 |
| `RPC_TIMEOUT_SECONDS` | RPC request timeout | 10 |

### Multiple Wallets

To use multiple wallets, add additional wallet private keys as environment variables:
```
WALLET_1_PRIVATE_KEY=key1
WALLET_2_PRIVATE_KEY=key2
WALLET_3_PRIVATE_KEY=key3
```

## Operation Schedule

The automation runs with the following schedule:
- First run: Executes immediately upon deployment
- Subsequent runs: Random time between 7 AM - 10 AM daily
- Each run performs 100 random transactions across configured protocols

## Security

- Never commit private keys to the repository
- Use environment variables for sensitive data
- Keep your `.env` file secure and never share it
- Add `.env` to `.gitignore`

## Monitoring

- Check the Zeabur logs for operation status
- The system logs:
  - Transaction execution results
  - RPC connection status
  - Scheduling information
  - Error messages and retries

## Troubleshooting

Common issues and solutions:

1. **RPC Connection Issues**
   - The system will automatically retry and rotate through available RPCs
   - Check RPC URLs are correct and accessible

2. **Transaction Failures**
   - Check wallet balance
   - Verify RPC connection
   - Check transaction logs in Zeabur dashboard

3. **Scheduling Issues**
   - Verify timezone settings in Zeabur
   - Check system logs for scheduling messages

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
