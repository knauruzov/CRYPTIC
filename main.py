#!/usr/bin/env python3
"""
DFIR CRYPTIC - Main Entry Point.

This script provides a command-line interface to the cryptocurrency forensic toolkit.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Import core modules
from src.config.settings import validate_env
from src.core.blockchain_client import BlockCypherClient, EtherscanAPIClient
from src.analyzers.transaction_analyzer import TransactionAnalyzer
from src.visualizers.graph_visualizer import TransactionGraphVisualizer
from src.utils.logger import setup_logger

# Set up logger
logger = setup_logger('main', 'main.log')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DFIR CRYPTIC - Cryptocurrency Forensic Analysis Toolkit'
    )
    
    # Main subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Address info command
    addr_parser = subparsers.add_parser('address', help='Get address information')
    addr_parser.add_argument('address', help='Blockchain address to analyze')
    addr_parser.add_argument('--blockchain', '-b', choices=['btc', 'eth'], default='btc',
                           help='Blockchain to analyze (default: btc)')
    
    # Transaction info command
    tx_parser = subparsers.add_parser('transaction', help='Get transaction information')
    tx_parser.add_argument('tx_hash', help='Transaction hash to analyze')
    tx_parser.add_argument('--blockchain', '-b', choices=['btc', 'eth'], default='btc',
                          help='Blockchain to analyze (default: btc)')
    
    # Graph analysis command
    graph_parser = subparsers.add_parser('graph', help='Create transaction graph')
    graph_parser.add_argument('address', help='Starting address for graph analysis')
    graph_parser.add_argument('--blockchain', '-b', choices=['btc', 'eth'], default='btc',
                            help='Blockchain to analyze (default: btc)')
    graph_parser.add_argument('--depth', '-d', type=int, default=2, 
                            help='Depth of transaction graph (default: 2)')
    graph_parser.add_argument('--max-addresses', '-m', type=int, default=100,
                            help='Maximum number of addresses to include (default: 100)')
    graph_parser.add_argument('--output', '-o', help='Output file for visualization')
    graph_parser.add_argument('--format', '-f', choices=['png', 'html', 'csv', 'graphml'], 
                            default='html', help='Output format (default: html)')
    
    # Trace funds command
    trace_parser = subparsers.add_parser('trace', help='Trace funds between addresses')
    trace_parser.add_argument('source', help='Source address')
    trace_parser.add_argument('target', nargs='*', help='Target address(es)')
    trace_parser.add_argument('--blockchain', '-b', choices=['btc', 'eth'], default='btc',
                            help='Blockchain to analyze (default: btc)')
    trace_parser.add_argument('--depth', '-d', type=int, default=3,
                            help='Depth of transaction graph (default: 3)')
    trace_parser.add_argument('--min-value', type=float, default=0,
                            help='Minimum value to consider (default: 0)')
    trace_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Mixer detection command
    mixer_parser = subparsers.add_parser('mixers', help='Detect potential mixer services')
    mixer_parser.add_argument('--blockchain', '-b', choices=['btc', 'eth'], default='btc',
                            help='Blockchain to analyze (default: btc)')
    mixer_parser.add_argument('--address', '-a', 
                            help='Starting address for analysis (optional)')
    mixer_parser.add_argument('--input-graph', '-i',
                            help='Input graph file from previous analysis (optional)')
    mixer_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Verbose mode
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()

def get_blockchain_client(blockchain):
    """Get the appropriate blockchain client."""
    if blockchain == 'btc':
        return BlockCypherClient(coin_symbol='btc')
    elif blockchain == 'eth':
        return EtherscanAPIClient()
    else:
        logger.error(f"Unsupported blockchain: {blockchain}")
        sys.exit(1)

def command_address_info(args):
    """Handle the address info command."""
    logger.info(f"Getting information for {args.blockchain} address: {args.address}")
    
    client = get_blockchain_client(args.blockchain)
    address_info = client.get_address_info(args.address)
    
    if address_info:
        print(f"\n=== Address Information for {args.address} ===")
        
        if args.blockchain == 'btc':
            # BlockCypher format
            balance_btc = address_info.get('final_balance', 0) / 1e8
            total_received = address_info.get('total_received', 0) / 1e8
            total_sent = address_info.get('total_sent', 0) / 1e8
            
            print(f"Balance: {balance_btc:.8f} BTC")
            print(f"Total Received: {total_received:.8f} BTC")
            print(f"Total Sent: {total_sent:.8f} BTC")
            print(f"Number of Transactions: {address_info.get('n_tx', 0)}")
            
        elif args.blockchain == 'eth':
            # Etherscan format
            print(f"Balance: {address_info.get('balance_eth'):.18f} ETH")
            print(f"Is Contract: {address_info.get('is_contract', False)}")
            
        # Recent transactions
        transactions = client.get_address_transactions(args.address, limit=5)
        
        if transactions:
            print("\nRecent Transactions:")
            for i, tx in enumerate(transactions[:5], 1):
                tx_hash = tx.get('hash') or tx.get('tx_hash') or tx.get('hash')
                
                if args.blockchain == 'btc':
                    if 'total' in tx:
                        value = tx.get('total', 0) / 1e8
                        print(f"{i}. Hash: {tx_hash}")
                        print(f"   Value: {value:.8f} BTC")
                    else:
                        print(f"{i}. Hash: {tx_hash}")
                        print(f"   Value: N/A")
                    confirmed = tx.get('confirmed', 'N/A')
                    print(f"   Confirmed: {confirmed}")
                    
                elif args.blockchain == 'eth':
                    value = int(tx.get('value', 0)) / 1e18
                    timestamp = tx.get('timeStamp', 'N/A')
                    print(f"{i}. Hash: {tx_hash}")
                    print(f"   Value: {value:.18f} ETH")
                    print(f"   From: {tx.get('from', 'N/A')}")
                    print(f"   To: {tx.get('to', 'N/A')}")
                    print(f"   Timestamp: {timestamp}")
        else:
            print("\nNo recent transactions found.")
    else:
        print(f"No information found for address: {args.address}")

def command_transaction_info(args):
    """Handle the transaction info command."""
    logger.info(f"Getting information for {args.blockchain} transaction: {args.tx_hash}")
    
    client = get_blockchain_client(args.blockchain)
    tx_info = client.get_transaction_info(args.tx_hash)
    
    if tx_info:
        print(f"\n=== Transaction Information for {args.tx_hash} ===")
        
        if args.blockchain == 'btc':
            # BlockCypher format
            value = tx_info.get('total', 0) / 1e8
            fees = tx_info.get('fees', 0) / 1e8
            confirmed = tx_info.get('confirmed', 'N/A')
            
            print(f"Value: {value:.8f} BTC")
            print(f"Fees: {fees:.8f} BTC")
            print(f"Confirmed: {confirmed}")
            
            # Inputs and outputs
            inputs = tx_info.get('inputs', [])
            outputs = tx_info.get('outputs', [])
            
            print(f"\nInputs ({len(inputs)}):")
            for i, input_data in enumerate(inputs, 1):
                addrs = input_data.get('addresses', ['N/A'])
                value = input_data.get('output_value', 0) / 1e8
                print(f"{i}. Address: {', '.join(addrs)}")
                print(f"   Value: {value:.8f} BTC")
            
            print(f"\nOutputs ({len(outputs)}):")
            for i, output_data in enumerate(outputs, 1):
                addrs = output_data.get('addresses', ['N/A'])
                value = output_data.get('value', 0) / 1e8
                print(f"{i}. Address: {', '.join(addrs)}")
                print(f"   Value: {value:.8f} BTC")
                
        elif args.blockchain == 'eth':
            # Etherscan format
            value = int(tx_info.get('value', 0)) / 1e18
            gas_price = int(tx_info.get('gasPrice', 0)) / 1e9
            gas_used = int(tx_info.get('gasUsed', 0))
            
            print(f"From: {tx_info.get('from', 'N/A')}")
            print(f"To: {tx_info.get('to', 'N/A')}")
            print(f"Value: {value:.18f} ETH")
            print(f"Gas Price: {gas_price:.9f} Gwei")
            print(f"Gas Used: {gas_used}")
            print(f"Block Number: {tx_info.get('blockNumber', 'N/A')}")
            
    else:
        print(f"No information found for transaction: {args.tx_hash}")

def command_graph_analysis(args):
    """Handle the graph analysis command."""
    logger.info(f"Creating transaction graph for {args.blockchain} address: {args.address}")
    
    client = get_blockchain_client(args.blockchain)
    analyzer = TransactionAnalyzer(client)
    
    print(f"Building transaction graph for {args.address} (depth: {args.depth})...")
    graph = analyzer.build_transaction_graph(
        args.address, 
        depth=args.depth,
        max_addresses=args.max_addresses
    )
    
    # Print graph statistics
    address_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'address']
    tx_nodes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'transaction']
    
    print("\nGraph Statistics:")
    print(f"Total Nodes: {graph.number_of_nodes()}")
    print(f"  - Addresses: {len(address_nodes)}")
    print(f"  - Transactions: {len(tx_nodes)}")
    print(f"Total Edges: {graph.number_of_edges()}")
    
    # Visualize graph
    visualizer = TransactionGraphVisualizer(graph)
    
    if args.format == 'png':
        if not args.output:
            args.output = f"transaction_graph_{args.address[:8]}_{args.blockchain}.png"
        
        print(f"Generating visualization as PNG: {args.output}")
        visualizer.visualize_matplotlib(args.output)
        
    elif args.format == 'html':
        if not args.output:
            args.output = f"transaction_graph_{args.address[:8]}_{args.blockchain}.html"
            
        print(f"Generating interactive visualization: {args.output}")
        visualizer.visualize_plotly(args.output)
        
    elif args.format in ['csv', 'graphml']:
        if not args.output:
            args.output = f"transaction_graph_{args.address[:8]}_{args.blockchain}"
            
        print(f"Exporting graph data: {args.output}")
        visualizer.export_graph_data(args.output, format=args.format)
    
    print(f"\nOutput saved to: {args.output}")
    print(f"Analysis complete for {args.address}.")

def command_trace_funds(args):
    """Handle the trace funds command."""
    logger.info(f"Tracing funds from {args.source} to {args.target or 'all destinations'}")
    
    client = get_blockchain_client(args.blockchain)
    analyzer = TransactionAnalyzer(client)
    
    print(f"Building transaction graph for {args.source} (depth: {args.depth})...")
    graph = analyzer.build_transaction_graph(
        args.source, 
        depth=args.depth,
        max_addresses=500  # Higher limit for tracing
    )
    
    # Trace funds
    print(f"Tracing funds from {args.source}...")
    paths = analyzer.trace_funds(
        args.source,
        target_addresses=args.target if args.target else None,
        min_value=args.min_value
    )
    
    # Display results
    if paths:
        print(f"\nFound {len(paths)} potential fund flow path(s):")
        
        for i, path_info in enumerate(paths[:10], 1):  # Show top 10
            path = path_info['path']
            value = path_info['value']
            length = path_info['length']
            
            if args.blockchain == 'btc':
                value_str = f"{value / 1e8:.8f} BTC"
            else:
                value_str = f"{value / 1e18:.18f} ETH"
                
            print(f"\nPath {i}:")
            print(f"  Value: {value_str}")
            print(f"  Length: {length} hop(s)")
            print("  Route:")
            
            for j, addr in enumerate(path):
                if j == 0:
                    print(f"    {j+1}. {addr} (Source)")
                elif j == len(path) - 1:
                    print(f"    {j+1}. {addr} (Destination)")
                else:
                    print(f"    {j+1}. {addr}")
        
        # Save results if output specified
        if args.output:
            import json
            
            # Prepare data for serialization (convert paths to strings)
            serializable_paths = []
            for path_info in paths:
                serializable_path = {
                    'path': [str(addr) for addr in path_info['path']],
                    'value': float(path_info['value']),
                    'length': path_info['length']
                }
                serializable_paths.append(serializable_path)
                
            with open(args.output, 'w') as f:
                json.dump(serializable_paths, f, indent=2)
                
            print(f"\nFull results saved to: {args.output}")
    else:
        print(f"No paths found from {args.source} to specified targets.")

def command_detect_mixers(args):
    """Handle the mixer detection command."""
    if args.input_graph:
        logger.info(f"Loading graph from {args.input_graph} for mixer detection")
        # Load graph from file
        import networkx as nx
        
        if args.input_graph.endswith('.graphml'):
            graph = nx.read_graphml(args.input_graph)
        elif args.input_graph.endswith('.gexf'):
            graph = nx.read_gexf(args.input_graph)
        else:
            logger.error(f"Unsupported graph file format: {args.input_graph}")
            print(f"Unsupported graph file format: {args.input_graph}")
            print("Please provide a .graphml or .gexf file.")
            return
            
        analyzer = TransactionAnalyzer(None)  # No client needed when loading existing graph
        analyzer.transaction_graph = graph
        
    elif args.address:
        logger.info(f"Building graph from {args.address} for mixer detection")
        client = get_blockchain_client(args.blockchain)
        analyzer = TransactionAnalyzer(client)
        
        print(f"Building transaction graph for {args.address}...")
        analyzer.build_transaction_graph(args.address, depth=3, max_addresses=300)
        
    else:
        logger.error("Either --address or --input-graph must be specified")
        print("Error: Either --address or --input-graph must be specified.")
        return
    
    print("Analyzing transaction patterns for potential mixers...")
    potential_mixers = analyzer.identify_potential_mixers()
    
    if potential_mixers:
        print(f"\nDetected {len(potential_mixers)} potential mixer addresses:")
        
        for i, mixer in enumerate(potential_mixers, 1):
            address = mixer['address']
            score = mixer['score']
            fan_in = mixer['fan_in']
            fan_out = mixer['fan_out']
            address_diversity = mixer['address_diversity']
            
            print(f"\n{i}. Address: {address}")
            print(f"   Mixer Score: {score:.2f}")
            print(f"   Fan-in: {fan_in}")
            print(f"   Fan-out: {fan_out}")
            print(f"   Address Diversity: {address_diversity}")
            print(f"   Time Regularity: {mixer['time_regularity']}")
            
        # Save results if output specified
        if args.output:
            import json
            
            # Prepare data for serialization
            serializable_mixers = []
            for mixer in potential_mixers:
                serializable_mixer = {k: (v if not isinstance(v, float) or not pd.isna(v) else "N/A") 
                                      for k, v in mixer.items()}
                serializable_mixers.append(serializable_mixer)
                
            with open(args.output, 'w') as f:
                json.dump(serializable_mixers, f, indent=2)
                
            print(f"\nFull results saved to: {args.output}")
    else:
        print("No potential mixer addresses detected.")

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    try:
        # Validate environment variables
        validate_env()
        
        # Execute requested command
        if args.command == 'address':
            command_address_info(args)
        elif args.command == 'transaction':
            command_transaction_info(args)
        elif args.command == 'graph':
            command_graph_analysis(args)
        elif args.command == 'trace':
            command_trace_funds(args)
        elif args.command == 'mixers':
            command_detect_mixers(args)
        else:
            print("Please specify a command. Use -h for help.")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        print("Check the log files for more details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 