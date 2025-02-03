import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='NullxNodePay Sentinel')
    parser.add_argument('-c', '--config', 
                       default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-proxy',
                       action='store_true',
                       help='Run without proxies')
    parser.add_argument('--single',
                       action='store_true',
                       help='Force single token mode')
    return parser.parse_args()