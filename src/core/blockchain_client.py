"""
Blockchain API client module.

This module provides classes for interacting with various blockchain APIs.
"""

import logging
from abc import ABC, abstractmethod
import requests
import json
from etherscan.client import Client as EtherscanClient

from ..config.settings import BLOCKCYPHER_API_KEY, ETHERSCAN_API_KEY, BLOCKCYPHER_BASE_URL

logger = logging.getLogger(__name__)

class BlockchainClient(ABC):
    """Abstract base class for blockchain API clients."""
    
    @abstractmethod
    def get_address_info(self, address):
        """Get information about an address."""
        pass
    
    @abstractmethod
    def get_transaction_info(self, tx_hash):
        """Get information about a transaction."""
        pass
    
    @abstractmethod
    def get_address_transactions(self, address, limit=50):
        """Get transactions for an address."""
        pass

class BlockCypherClient(BlockchainClient):
    """Client for the BlockCypher API."""
    
    def __init__(self, api_key=None, coin_symbol='btc', chain='main'):
        """
        Initialize the BlockCypher client.
        
        Args:
            api_key (str, optional): BlockCypher API key. Defaults to the key from settings.
            coin_symbol (str, optional): Coin symbol (btc, eth, ltc, etc.). Defaults to 'btc'.
            chain (str, optional): Blockchain network (main, test, etc.). Defaults to 'main'.
        """
        self.api_key = api_key or BLOCKCYPHER_API_KEY
        self.coin_symbol = coin_symbol
        self.chain = chain
        self.base_url = f"{BLOCKCYPHER_BASE_URL}/{self.coin_symbol}/{self.chain}"
        
        if not self.api_key:
            logger.warning("BlockCypher API key not set. API call limits may apply.")
    
    def _make_request(self, endpoint, params=None):
        """
        Make a request to the BlockCypher API.
        
        Args:
            endpoint (str): API endpoint to call.
            params (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            dict: API response.
        """
        if params is None:
            params = {}
            
        # Add API key to params
        if self.api_key:
            params['token'] = self.api_key
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    def get_address_info(self, address):
        """
        Get information about an address.
        
        Args:
            address (str): The blockchain address to query.
            
        Returns:
            dict: Address information.
        """
        return self._make_request(f"addrs/{address}")
    
    def get_transaction_info(self, tx_hash):
        """
        Get information about a transaction.
        
        Args:
            tx_hash (str): The transaction hash to query.
            
        Returns:
            dict: Transaction information.
        """
        return self._make_request(f"txs/{tx_hash}")
    
    def get_address_transactions(self, address, limit=50):
        """
        Get transactions for an address.
        
        Args:
            address (str): The blockchain address to query.
            limit (int, optional): Maximum number of transactions to return. Defaults to 50.
            
        Returns:
            list: List of transactions.
        """
        # Get the address details with transactions
        address_info = self.get_address_info(address)
        
        if not address_info:
            return []
            
        # Get transaction hashes from txrefs
        tx_refs = address_info.get('txrefs', [])
        
        # If no txrefs, try unconfirmed transactions
        if not tx_refs:
            tx_refs = address_info.get('unconfirmed_txrefs', [])
            
        if not tx_refs:
            return []
            
        # Get full transaction details for each transaction
        transactions = []
        for tx_ref in tx_refs[:min(5, len(tx_refs))]:  # Limit to 5 to avoid rate limiting
            tx_hash = tx_ref.get('tx_hash')
            if tx_hash:
                tx_info = self.get_transaction_info(tx_hash)
                if tx_info:
                    transactions.append(tx_info)
                    
        return transactions

class EtherscanAPIClient(BlockchainClient):
    """Client for the Etherscan API."""
    
    def __init__(self, api_key=None, network='mainnet'):
        """
        Initialize the Etherscan client.
        
        Args:
            api_key (str, optional): Etherscan API key. Defaults to the key from settings.
            network (str, optional): Ethereum network (mainnet, ropsten, etc.). Defaults to 'mainnet'.
        """
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.network = network
        
        if not self.api_key:
            logger.warning("Etherscan API key not set. API call limits may apply.")
        
        self.client = EtherscanClient(api_key=self.api_key)
    
    def get_address_info(self, address):
        """
        Get information about an Ethereum address.
        
        Args:
            address (str): The Ethereum address to query.
            
        Returns:
            dict: Address information including balance and code.
        """
        try:
            # Combine balance and contract status in one result
            balance_wei = self.client.get_eth_balance(address)
            balance_eth = int(balance_wei) / 10**18
            
            # Check if the address is a contract
            code = self.client.get_code(address)
            is_contract = code != '0x'
            
            return {
                'address': address,
                'balance_wei': balance_wei,
                'balance_eth': balance_eth,
                'is_contract': is_contract,
                'code': code if is_contract else None
            }
        except Exception as e:
            logger.error(f"Error getting address info for {address}: {str(e)}")
            return None
    
    def get_transaction_info(self, tx_hash):
        """
        Get information about an Ethereum transaction.
        
        Args:
            tx_hash (str): The transaction hash to query.
            
        Returns:
            dict: Transaction information.
        """
        try:
            return self.client.get_proxy_transaction_by_hash(tx_hash)
        except Exception as e:
            logger.error(f"Error getting transaction info for {tx_hash}: {str(e)}")
            return None
    
    def get_address_transactions(self, address, limit=50):
        """
        Get transactions for an Ethereum address.
        
        Args:
            address (str): The Ethereum address to query.
            limit (int, optional): Maximum number of transactions to return. Defaults to 50.
            
        Returns:
            list: List of transactions.
        """
        try:
            # Check if the address is a contract
            code = self.client.get_code(address)
            is_contract = code != '0x'
            
            if is_contract:
                # For contracts we need to get both internal and normal transactions
                normal_txs = self.client.get_normal_txs_by_address(
                    address,
                    startblock=0,
                    endblock=99999999,
                    sort='desc'
                )
                
                internal_txs = self.client.get_internal_txs_by_address(
                    address,
                    startblock=0,
                    endblock=99999999,
                    sort='desc'
                )
                
                # Combine and sort by timestamp
                all_txs = normal_txs + internal_txs
                all_txs.sort(key=lambda x: int(x.get('timeStamp', 0)), reverse=True)
                
                return all_txs[:limit]
            else:
                # For regular addresses, just get normal transactions
                return self.client.get_normal_txs_by_address(
                    address,
                    startblock=0,
                    endblock=99999999,
                    sort='desc',
                    page=1,
                    offset=limit
                )
        except Exception as e:
            logger.error(f"Error getting transactions for address {address}: {str(e)}")
            return [] 