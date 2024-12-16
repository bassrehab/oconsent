
from typing import Dict, Optional, Union
from datetime import datetime
import requests
from bitcoin import SelectParams
from bitcoin.rpc import Proxy
from bitcoin.core import COIN, lx, b2x, b2lx
from bitcoin.wallet import CBitcoinAddress

class BitcoinClient:
    """Client for interacting with Bitcoin blockchain for timestamping."""
    # Example usage:
    """
    client = BitcoinClient(
        rpc_url='http://localhost:8332',
        rpc_user='user',
        rpc_password='pass'
    )

    # Create timestamp
    timestamp = client.create_timestamp('1234567890abcdef')

    # Verify timestamp
    is_valid = client.verify_timestamp(
        timestamp['tx_id'],
        '1234567890abcdef'
    )
    """
    
    def __init__(
        self,
        rpc_url: str,
        rpc_user: Optional[str] = None,
        rpc_password: Optional[str] = None,
        network: str = 'mainnet'
    ):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        
        # Set network
        SelectParams(network)
        
        # Initialize RPC connection
        self.proxy = Proxy(
            service_url=rpc_url,
            rpc_user=rpc_user,
            rpc_password=rpc_password
        )
    
    def create_timestamp(self, data_hash: str) -> Dict[str, Union[str, int]]:
        """Creates a Bitcoin timestamp for a data hash."""
        # Create OP_RETURN transaction
        script = f"OP_RETURN {data_hash}"
        raw_tx = self.proxy.createrawtransaction([], {script: 0})
        
        # Sign transaction
        signed_tx = self.proxy.signrawtransaction(raw_tx)
        
        # Send transaction
        tx_id = self.proxy.sendrawtransaction(signed_tx['hex'])
        
        # Get block information
        tx_info = self.proxy.gettransaction(tx_id)
        block_hash = tx_info['blockhash']
        block_info = self.proxy.getblock(block_hash)
        
        return {
            'tx_id': b2lx(tx_id),
            'block_hash': b2lx(block_hash),
            'block_height': block_info['height'],
            'timestamp': block_info['time']
        }
    
    def verify_timestamp(
        self,
        tx_id: str,
        data_hash: str,
        min_confirmations: int = 6
    ) -> bool:
        """Verifies a Bitcoin timestamp."""
        try:
            # Get transaction information
            tx_info = self.proxy.gettransaction(lx(tx_id))
            
            # Check confirmations
            if tx_info['confirmations'] < min_confirmations:
                return False
            
            # Get raw transaction
            raw_tx = self.proxy.getrawtransaction(lx(tx_id))
            
            # Verify OP_RETURN data
            for output in raw_tx.vout:
                script = output.scriptPubKey
                if script.is_op_return():
                    stored_hash = b2x(script[1:])
                    if stored_hash == data_hash:
                        return True
            
            return False
        except Exception:
            return False
    
    def get_block_time(self, block_hash: str) -> datetime:
        """Gets the timestamp of a specific block."""
        block_info = self.proxy.getblock(lx(block_hash))
        return datetime.fromtimestamp(block_info['time'])


