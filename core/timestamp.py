# oconsent/core/timestamp.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict
import requests
import json
from web3 import Web3

class TimestampProvider(ABC):
    """Abstract base class for timestamp providers."""
    
    @abstractmethod
    def get_timestamp(self) -> Dict:
        """Gets a verifiable timestamp."""
        pass
    
    @abstractmethod
    def verify_timestamp(self, timestamp_proof: Dict) -> bool:
        """Verifies a timestamp proof."""
        pass

class NISTBeaconProvider(TimestampProvider):
    """NIST Randomness Beacon timestamp provider."""
    
    def __init__(self):
        self.base_url = "https://beacon.nist.gov/beacon/2.0/pulse/last"
    
    def get_timestamp(self) -> Dict:
        response = requests.get(self.base_url)
        if response.status_code != 200:
            raise RuntimeError("Failed to get NIST timestamp")
            
        data = response.json()
        return {
            'timestamp': data['pulse']['timeStamp'],
            'randomness': data['pulse']['randomValue'],
            'signature': data['pulse']['signature'],
            'type': 'nist'
        }
    
    def verify_timestamp(self, timestamp_proof: Dict) -> bool:
        if timestamp_proof.get('type') != 'nist':
            return False
            
        # Verify against NIST beacon
        url = f"https://beacon.nist.gov/beacon/2.0/pulse/time/{timestamp_proof['timestamp']}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        return (
            data['pulse']['randomValue'] == timestamp_proof['randomness'] and
            data['pulse']['signature'] == timestamp_proof['signature']
        )

class BitcoinTimestampProvider(TimestampProvider):
    """Bitcoin blockchain timestamp provider."""
    
    def __init__(self, node_url: str):
        self.web3 = Web3(Web3.HTTPProvider(node_url))
    
    def get_timestamp(self) -> Dict:
        block = self.web3.eth.get_block('latest')
        return {
            'timestamp': block['timestamp'],
            'block_hash': block['hash'].hex(),
            'block_number': block['number'],
            'type': 'bitcoin'
        }
    
    def verify_timestamp(self, timestamp_proof: Dict) -> bool:
        if timestamp_proof.get('type') != 'bitcoin':
            return False
            
        try:
            block = self.web3.eth.get_block(timestamp_proof['block_number'])
            return (
                block['timestamp'] == timestamp_proof['timestamp'] and
                block['hash'].hex() == timestamp_proof['block_hash']
            )
        except Exception:
            return False

class TimestampService:
    """Manages timestamp operations using multiple providers."""
    
    def __init__(self, providers: Optional[Dict[str, TimestampProvider]] = None):
        self.providers = providers or {
            'nist': NISTBeaconProvider(),
            'bitcoin': BitcoinTimestampProvider('http://localhost:8332')
        }
    
    def timestamp(self, agreement: 'ConsentAgreement') -> str:
        """Creates a timestamp proof for a consent agreement."""
        proofs = {}
        for name, provider in self.providers.items():
            try:
                proofs[name] = provider.get_timestamp()
            except Exception as e:
                print(f"Failed to get timestamp from {name}: {e}")
                
        return json.dumps(proofs)
    
    def verify_timestamp(self, agreement: 'ConsentAgreement') -> bool:
        """Verifies timestamp proofs for a consent agreement."""
        if not agreement.timestamp_proof:
            return False
            
        try:
            proofs = json.loads(agreement.timestamp_proof)
            
            # Require at least one valid proof
            valid_proofs = 0
            for name, proof in proofs.items():
                if name in self.providers:
                    if self.providers[name].verify_timestamp(proof):
                        valid_proofs += 1
                        
            return valid_proofs > 0
        except Exception:
            return False