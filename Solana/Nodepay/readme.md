# NullxNodePay Sentinel

## Requirements

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/0xGery/Bot.git
    cd Bot/Solana/Nodepay
    ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Add your token to `data/token.txt`:
   ```bash
   nano data/token.txt
   ```
3. Add proxies to `data/proxies.txt`:
    ```bash
    nano data/proxies.txt
    ```
    
## Usage
Run the sentinel:
  ```bash
  python main.py
  ```
### Operation Modes

1. **Single Account**
   - One account with multiple proxies

2. **Multi Account**
   - Multiple accounts with proxy distribution

## Security Notes
- Do not commit your token.txt and proxies.txt file 
- Add data/ to your .gitignore file

## Contributing
- Fork the repository
- Create a new branch
- Make your changes
- Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**NullxGery** - [GitHub](https://github.com/0xGery)
