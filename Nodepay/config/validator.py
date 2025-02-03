import os
import yaml
from utils.exceptions import SentinelException

class ConfigValidator:
    @staticmethod
    def validate_config(config_path):
        if not os.path.exists(config_path):
            raise SentinelException(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        required_sections = ['monitor', 'proxy', 'dashboard']
        for section in required_sections:
            if section not in config:
                raise SentinelException(f"Missing required config section: {section}")

        return config

    @staticmethod
    def validate_files():
        required_files = [
            'data/token.txt',
            'data/proxies.txt'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise SentinelException(f"Required file not found: {file_path}")
