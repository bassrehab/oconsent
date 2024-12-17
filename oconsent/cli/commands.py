# oconsent/cli/commands.py

import click
from datetime import datetime, timedelta
import json
from typing import Dict, List

from oconsent.core.consent import ConsentManager, ConsentPurpose
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.crypto.zk_proofs import ProofGenerator
from oconsent.core.timestamp import TimestampService

@click.group()
def cli():
    """OConsent - Open Consent Protocol CLI"""
    pass

@cli.command()
@click.option('--subject-id', required=True, help='ID of the data subject')
@click.option('--processor-id', required=True, help='ID of the data processor')
@click.option('--purposes', required=True, help='JSON file containing consent purposes')
@click.option('--valid-days', default=365, help='Number of days the consent is valid for')
@click.option('--metadata', help='Optional JSON metadata')
def create_consent(
    subject_id: str,
    processor_id: str,
    purposes: str,
    valid_days: int,
    metadata: str
):
    """Creates a new consent agreement."""
    # Initialize components
    ethereum_client = EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...',  # Contract address would be set in config
        private_key='0x...'  # Private key would be set in config
    )
    
    proof_generator = ProofGenerator('path/to/snark/params')
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Load purposes from JSON file
    with open(purposes) as f:
        purposes_data = json.load(f)
    
    consent_purposes = [
        ConsentPurpose(
            id=p['id'],
            name=p['name'],
            description=p['description'],
            retention_period=p['retention_period'],
            created_at=datetime.utcnow()
        )
        for p in purposes_data
    ]
    
    # Load metadata if provided
    metadata_dict = {}
    if metadata:
        with open(metadata) as f:
            metadata_dict = json.load(f)
    
    # Create agreement
    agreement = consent_manager.create_agreement(
        subject_id=subject_id,
        processor_id=processor_id,
        purposes=consent_purposes,
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=valid_days),
        metadata=metadata_dict
    )
    
    click.echo(f"Created consent agreement: {agreement.id}")
    click.echo(json.dumps(agreement.__dict__, default=str, indent=2))

@cli.command()
@click.option('--agreement-id', required=True, help='ID of the consent agreement')
def revoke_consent(agreement_id: str):
    """Revokes an existing consent agreement."""
    # Initialize components (similar to create_consent)
    ethereum_client = EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...',
        private_key='0x...'
    )
    
    proof_generator = ProofGenerator('path/to/snark/params')
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Revoke agreement
    agreement = consent_manager.revoke_agreement(agreement_id)
    click.echo(f"Revoked consent agreement: {agreement.id}")
    click.echo(json.dumps(agreement.__dict__, default=str, indent=2))

@cli.command()
@click.option('--agreement-id', required=True, help='ID of the consent agreement')
@click.option('--purpose-id', required=True, help='ID of the purpose to verify')
@click.option('--processor-id', required=True, help='ID of the processor')
def verify_consent(agreement_id: str, purpose_id: str, processor_id: str):
    """Verifies if consent exists and is valid for a specific purpose."""
    # Initialize components
    config = load_config()
    ethereum_client = EthereumClient(
        provider_url=config['ethereum']['provider_url'],
        contract_address=config['ethereum']['contract_address']
    )
    
    proof_generator = ProofGenerator(config['snark']['params_path'])
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Verify consent
    is_valid = consent_manager.verify_consent(
        agreement_id=agreement_id,
        purpose_id=purpose_id,
        processor_id=processor_id
    )
    
    if is_valid:
        click.echo(click.style("✓ Consent is valid", fg="green"))
        
        # Get additional details
        agreement = ethereum_client.get_agreement(agreement_id)
        if agreement:
            # Find the specific purpose
            purpose = next((p for p in agreement.purposes if p.id == purpose_id), None)
            if purpose:
                click.echo("\nConsent Details:")
                click.echo(f"Subject ID: {agreement.subject_id}")
                click.echo(f"Valid From: {agreement.valid_from}")
                click.echo(f"Valid Until: {agreement.valid_until or 'No expiration'}")
                click.echo(f"\nPurpose Details:")
                click.echo(f"Name: {purpose.name}")
                click.echo(f"Description: {purpose.description}")
                click.echo(f"Retention Period: {timedelta(seconds=purpose.retention_period)}")
    else:
        click.echo(click.style("✗ Consent is not valid", fg="red"))
        
        # Try to provide more specific error information
        agreement = ethereum_client.get_agreement(agreement_id)
        if not agreement:
            click.echo("Reason: Agreement not found")
        elif agreement.status != "active":
            click.echo(f"Reason: Agreement status is {agreement.status}")
        elif agreement.processor_id != processor_id:
            click.echo("Reason: Processor ID mismatch")
        elif not any(p.id == purpose_id for p in agreement.purposes):
            click.echo("Reason: Purpose not found in agreement")
        elif agreement.valid_until and agreement.valid_until < datetime.utcnow():
            click.echo("Reason: Agreement has expired")
        else:
            click.echo("Reason: Invalid proofs or timestamps")


@cli.command()
@click.option('--subject-id', help='Filter by subject ID')
@click.option('--processor-id', help='Filter by processor ID')
@click.option('--status', type=click.Choice(['active', 'revoked', 'expired']), help='Filter by status')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('--output', help='Output file path (for CSV/JSON)')
def list_agreements(
    subject_id: Optional[str],
    processor_id: Optional[str],
    status: Optional[str],
    format: str,
    output: Optional[str]
):
    """Lists consent agreements based on filters."""
    # Initialize components
    config = load_config()
    ethereum_client = EthereumClient(
        provider_url=config['ethereum']['provider_url'],
        contract_address=config['ethereum']['contract_address'],
        private_key=config['ethereum']['private_key']
    )
    
    proof_generator = ProofGenerator(config['snark']['params_path'])
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Get agreements
    agreements = consent_manager.list_agreements(
        subject_id=subject_id,
        processor_id=processor_id,
        status=status
    )
    
    # Prepare data for output
    data = []
    for agreement in agreements:
        data.append({
            'id': agreement.id,
            'subject_id': agreement.subject_id,
            'processor_id': agreement.processor_id,
            'status': agreement.status,
            'valid_from': agreement.valid_from.isoformat(),
            'valid_until': agreement.valid_until.isoformat() if agreement.valid_until else 'Never',
            'purposes': len(agreement.purposes)
        })
    
    # Output based on format
    if format == 'table':
        if data:
            click.echo(tabulate(data, headers='keys', tablefmt='grid'))
        else:
            click.echo("No agreements found matching the criteria.")
            
    elif format == 'json':
        if output:
            with open(output, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            click.echo(json.dumps(data, indent=2))
            
    elif format == 'csv':
        if not data:
            click.echo("No agreements found matching the criteria.")
            return
            
        headers = data[0].keys()
        if output:
            with open(output, 'w', newline='') as f:
                writer = csv.DictWriter(f, headers)
                writer.writeheader()
                writer.writerows(data)
        else:
            writer = csv.DictWriter(click.get_text_stream('stdout'), headers)
            writer.writeheader()
            writer.writerows(data)

@cli.command()
@click.option('--agreement-id', required=True, help='ID of the consent agreement')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json', help='Export format')
@click.option('--output', help='Output file path')
@click.option('--include-proofs/--no-proofs', default=False, help='Include cryptographic proofs')
def export_agreement(agreement_id: str, format: str, output: Optional[str], include_proofs: bool):
    """Exports a consent agreement in the specified format."""
    config = load_config()
    ethereum_client = EthereumClient(
        provider_url=config['ethereum']['provider_url'],
        contract_address=config['ethereum']['contract_address']
    )
    
    proof_generator = ProofGenerator(config['snark']['params_path'])
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Get agreement
    agreement = ethereum_client.get_agreement(agreement_id)
    if not agreement:
        click.echo(f"Agreement {agreement_id} not found", err=True)
        return
    
    # Prepare export data
    export_data = {
        'id': agreement.id,
        'subject_id': agreement.subject_id,
        'processor_id': agreement.processor_id,
        'status': agreement.status,
        'valid_from': agreement.valid_from.isoformat(),
        'valid_until': agreement.valid_until.isoformat() if agreement.valid_until else None,
        'purposes': [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'retention_period': p.retention_period
            }
            for p in agreement.purposes
        ],
        'metadata': agreement.metadata
    }
    
    if include_proofs:
        export_data['proofs'] = {
            'consent_proof': agreement.proof_id,
            'timestamp_proof': agreement.timestamp_proof
        }
    
    # Export based on format
    if format == 'json':
        output_data = json.dumps(export_data, indent=2)
    else:  # yaml
        import yaml
        output_data = yaml.dump(export_data, default_flow_style=False)
    
    if output:
        with open(output, 'w') as f:
            f.write(output_data)
        click.echo(f"Agreement exported to {output}")
    else:
        click.echo(output_data)

@cli.command()
@click.option('--agreement-id', required=True, help='ID of the consent agreement')
@click.option('--purpose-id', required=True, help='ID of the purpose to add')
@click.option('--name', required=True, help='Name of the purpose')
@click.option('--description', required=True, help='Description of the purpose')
@click.option('--retention-period', type=int, required=True, help='Retention period in seconds')
def add_purpose(
    agreement_id: str,
    purpose_id: str,
    name: str,
    description: str,
    retention_period: int
):
    """Adds a new purpose to an existing consent agreement."""
    config = load_config()
    ethereum_client = EthereumClient(
        provider_url=config['ethereum']['provider_url'],
        contract_address=config['ethereum']['contract_address'],
        private_key=config['ethereum']['private_key']
    )
    
    proof_generator = ProofGenerator(config['snark']['params_path'])
    timestamp_service = TimestampService()
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )
    
    # Get existing agreement
    agreement = ethereum_client.get_agreement(agreement_id)
    if not agreement:
        click.echo(f"Agreement {agreement_id} not found", err=True)
        return
    
    # Create new purpose
    new_purpose = ConsentPurpose(
        id=purpose_id,
        name=name,
        description=description,
        retention_period=retention_period,
        created_at=datetime.utcnow()
    )
    
    # Add purpose to agreement
    agreement.purposes.append(new_purpose)
    
    # Update proofs
    agreement.proof_id = proof_generator.generate_consent_proof(agreement)
    agreement.timestamp_proof = timestamp_service.timestamp(agreement)
    
    # Store updated agreement
    ethereum_client.update_agreement(agreement)
    
    click.echo(f"Added purpose {purpose_id} to agreement {agreement_id}")

@cli.command()
@click.option('--config-file', type=click.Path(), help='Path to configuration file')
@click.option('--ethereum-url', help='Ethereum provider URL')
@click.option('--contract-address', help='Contract address')
@click.option('--private-key', help='Private key for transactions')
def configure(
    config_file: Optional[str],
    ethereum_url: Optional[str],
    contract_address: Optional[str],
    private_key: Optional[str]
):
    """Configures the CLI with connection details."""
    if config_file:
        if not os.path.exists(config_file):
            click.echo(f"Config file {config_file} not found", err=True)
            return
        
        # Load and validate config file
        with open(config_file) as f:
            config = json.load(f)
    else:
        # Create config interactively
        config = {}
        config['ethereum'] = {
            'provider_url': ethereum_url or click.prompt('Ethereum provider URL', type=str),
            'contract_address': contract_address or click.prompt('Contract address', type=str),
            'private_key': private_key or click.prompt('Private key', type=str, hide_input=True)
        }
        
        config['snark'] = {
            'params_path': click.prompt('Path to SNARK parameters', type=str)
        }
    
    # Save configuration
    config_dir = click.get_app_dir('oconsent')
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"Configuration saved to {config_path}")

if __name__ == '__main__':
    cli()
    