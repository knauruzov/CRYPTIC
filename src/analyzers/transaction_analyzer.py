"""
Transaction analyzer module.

This module provides classes for analyzing blockchain transactions and identifying patterns.
"""

import logging
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)

class TransactionAnalyzer:
    """
    Analyzes blockchain transactions to identify patterns and relationships.
    """
    
    def __init__(self, blockchain_client):
        """
        Initialize the transaction analyzer.
        
        Args:
            blockchain_client: A blockchain client instance.
        """
        self.client = blockchain_client
        self.transaction_graph = nx.DiGraph()
    
    def build_transaction_graph(self, target_address, depth=2, max_addresses=100):
        """
        Build a directed graph of transactions for a given address.
        
        Args:
            target_address (str): The starting address to analyze.
            depth (int, optional): How many levels of transactions to trace. Defaults to 2.
            max_addresses (int, optional): Maximum number of addresses to include. Defaults to 100.
            
        Returns:
            networkx.DiGraph: A directed graph representing the transaction flows.
        """
        addresses_to_process = [(target_address, 0)]  # (address, depth)
        processed_addresses = set()
        
        self.transaction_graph.add_node(
            target_address,
            type='address',
            is_target=True,
            depth=0
        )
        
        while addresses_to_process and len(processed_addresses) < max_addresses:
            current_address, current_depth = addresses_to_process.pop(0)
            
            if current_address in processed_addresses:
                continue
                
            processed_addresses.add(current_address)
            
            if current_depth >= depth:
                continue
            
            # Get transactions for the current address
            transactions = self.client.get_address_transactions(current_address)
            
            for tx in transactions:
                self._process_transaction(tx, current_address, current_depth, addresses_to_process)
                
        return self.transaction_graph
    
    def _process_transaction(self, tx, current_address, current_depth, addresses_to_process):
        """
        Process a transaction and add it to the graph.
        
        Args:
            tx (dict): Transaction data.
            current_address (str): The address being processed.
            current_depth (int): Current depth in the analysis.
            addresses_to_process (list): List of addresses to be processed.
        """
        # Implementation will vary based on the blockchain and client
        # This is a generic implementation that needs to be adapted
        
        # Handle None or empty transaction
        if not tx:
            logger.warning(f"Empty transaction data in _process_transaction")
            return
        
        # Extract transaction ID
        tx_hash = tx.get('hash') or tx.get('tx_hash')
        
        if not tx_hash:
            logger.warning(f"Could not determine transaction hash from {tx}")
            return
            
        # Add transaction node if it doesn't exist
        if not self.transaction_graph.has_node(tx_hash):
            # Try to get timestamp
            timestamp = None
            if 'confirmed' in tx:
                timestamp = tx['confirmed']
            elif 'timeStamp' in tx:
                timestamp = datetime.fromtimestamp(int(tx['timeStamp']))
                
            self.transaction_graph.add_node(
                tx_hash,
                type='transaction',
                timestamp=timestamp,
                value=tx.get('value') or tx.get('total'),
                depth=current_depth
            )
        
        # Process inputs
        inputs = self._extract_inputs(tx)
        for input_addr in inputs:
            if input_addr not in self.transaction_graph:
                self.transaction_graph.add_node(
                    input_addr,
                    type='address',
                    is_target=(input_addr == current_address),
                    depth=current_depth
                )
                
            # Add edge from address to transaction (spending)
            self.transaction_graph.add_edge(
                input_addr, 
                tx_hash,
                type='input',
                value=inputs.get(input_addr, 0)
            )
            
            # Add to processing queue if not the current address
            if input_addr != current_address:
                addresses_to_process.append((input_addr, current_depth + 1))
        
        # Process outputs
        outputs = self._extract_outputs(tx)
        for output_addr in outputs:
            if output_addr not in self.transaction_graph:
                self.transaction_graph.add_node(
                    output_addr,
                    type='address',
                    is_target=(output_addr == current_address),
                    depth=current_depth
                )
                
            # Add edge from transaction to address (receiving)
            self.transaction_graph.add_edge(
                tx_hash,
                output_addr,
                type='output',
                value=outputs.get(output_addr, 0)
            )
            
            # Add to processing queue if not the current address
            if output_addr != current_address:
                addresses_to_process.append((output_addr, current_depth + 1))
    
    def _extract_inputs(self, tx):
        """
        Extract input addresses and values from a transaction.
        
        Args:
            tx (dict): Transaction data.
            
        Returns:
            dict: Dictionary mapping address to value.
        """
        inputs = {}
        
        if not tx:
            return inputs
        
        # BlockCypher format
        if 'inputs' in tx:
            for input_data in tx.get('inputs', []):
                prev_addrs = input_data.get('addresses', [])
                # Make sure addresses is not None
                if prev_addrs is None:
                    continue
                for addr in prev_addrs:
                    if addr:  # Skip None or empty addresses
                        inputs[addr] = input_data.get('output_value', 0)
        
        # Etherscan format
        elif 'from' in tx and tx['from']:  # Make sure 'from' is not None or empty
            inputs[tx['from']] = tx.get('value', 0)
            
        return inputs
    
    def _extract_outputs(self, tx):
        """
        Extract output addresses and values from a transaction.
        
        Args:
            tx (dict): Transaction data.
            
        Returns:
            dict: Dictionary mapping address to value.
        """
        outputs = {}
        
        if not tx:
            return outputs
        
        # BlockCypher format
        if 'outputs' in tx:
            for output_data in tx.get('outputs', []):
                out_addrs = output_data.get('addresses', [])
                # Make sure addresses is not None
                if out_addrs is None:
                    continue
                for addr in out_addrs:
                    if addr:  # Skip None or empty addresses
                        outputs[addr] = output_data.get('value', 0)
        
        # Etherscan format
        elif 'to' in tx and tx['to']:  # Make sure 'to' is not None or empty
            outputs[tx['to']] = tx.get('value', 0)
            
        return outputs
    
    def identify_potential_mixers(self, graph=None):
        """
        Identify addresses that may be mixers based on transaction patterns.
        
        Args:
            graph (networkx.DiGraph, optional): Transaction graph to analyze. 
                                               Defaults to the last built graph.
                
        Returns:
            list: List of potential mixer addresses with their scores.
        """
        if graph is None:
            graph = self.transaction_graph
            
        potential_mixers = []
        
        for node in graph.nodes():
            node_data = graph.nodes[node]
            
            # Only analyze address nodes
            if node_data.get('type') != 'address':
                continue
                
            # Get in and out transactions
            in_txs = [edge for edge in graph.in_edges(node) if graph.nodes[edge[0]].get('type') == 'transaction']
            out_txs = [edge for edge in graph.out_edges(node) if graph.nodes[edge[1]].get('type') == 'transaction']
            
            # Skip addresses with too few transactions
            if len(in_txs) < 3 or len(out_txs) < 3:
                continue
                
            # Calculate metrics
            fan_in = len(set(edge[0] for edge in in_txs))  # Unique input transactions
            fan_out = len(set(edge[1] for edge in out_txs))  # Unique output transactions
            
            # Get all inbound and outbound addresses
            in_addresses = set()
            for tx_hash, _ in in_txs:
                for source, _ in graph.in_edges(tx_hash):
                    if graph.nodes[source].get('type') == 'address':
                        in_addresses.add(source)
                        
            out_addresses = set()
            for _, tx_hash in out_txs:
                for _, target in graph.out_edges(tx_hash):
                    if graph.nodes[target].get('type') == 'address':
                        out_addresses.add(target)
            
            # Calculate address diversity
            address_diversity = len(in_addresses.union(out_addresses))
            
            # Time-based analysis for transaction timing patterns
            timestamps = []
            for tx_edge in in_txs + out_txs:
                tx_node = tx_edge[0] if tx_edge in in_txs else tx_edge[1]
                tx_data = graph.nodes[tx_node]
                if 'timestamp' in tx_data and tx_data['timestamp']:
                    timestamps.append(tx_data['timestamp'])
            
            # Calculate time-based metrics if timestamps are available
            time_regularity = 0
            if len(timestamps) > 1:
                # Sort timestamps
                timestamps.sort()
                
                # Calculate time differences between consecutive transactions
                time_diffs = []
                for i in range(1, len(timestamps)):
                    if isinstance(timestamps[i], datetime) and isinstance(timestamps[i-1], datetime):
                        diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                        time_diffs.append(diff)
                
                # Calculate coefficient of variation (lower means more regular patterns)
                if time_diffs:
                    import numpy as np
                    mean_diff = np.mean(time_diffs)
                    std_diff = np.std(time_diffs)
                    if mean_diff > 0:
                        time_regularity = std_diff / mean_diff
            
            # Mixer score calculation (higher is more suspicious)
            # Factors:
            # - High fan-in and fan-out
            # - High address diversity
            # - Low time variance (regular patterns)
            mixer_score = (fan_in * 0.3) + (fan_out * 0.3) + (address_diversity * 0.2)
            
            if time_regularity > 0:
                # Lower time_regularity (more regular patterns) increases the score
                mixer_score += (1 / time_regularity) * 0.2
            
            if mixer_score > 10:  # Arbitrary threshold, should be tuned
                potential_mixers.append({
                    'address': node,
                    'score': mixer_score,
                    'fan_in': fan_in,
                    'fan_out': fan_out,
                    'address_diversity': address_diversity,
                    'time_regularity': time_regularity if time_regularity > 0 else 'N/A'
                })
        
        # Sort by score in descending order
        potential_mixers.sort(key=lambda x: x['score'], reverse=True)
        return potential_mixers
    
    def trace_funds(self, source_address, target_addresses=None, min_value=0):
        """
        Trace funds from a source address to potential target addresses.
        
        Args:
            source_address (str): The source address to trace funds from.
            target_addresses (list, optional): List of target addresses to trace to.
                                              If None, all paths are returned.
            min_value (float, optional): Minimum value to consider for tracing.
            
        Returns:
            list: List of paths from source to targets.
        """
        graph = self.transaction_graph
        
        # Ensure we're working with a graph that has the source address
        if source_address not in graph:
            logger.error(f"Source address {source_address} not in the graph")
            return []
        
        # Create a simplified graph for path finding (address -> address)
        simplified_graph = nx.DiGraph()
        
        # For each transaction in the graph, create direct connections between addresses
        for node in graph.nodes():
            node_data = graph.nodes[node]
            
            if node_data.get('type') != 'transaction':
                continue
                
            # Get input addresses and values
            inputs = {}
            for src, _ in graph.in_edges(node):
                if graph.nodes[src].get('type') == 'address':
                    edge_data = graph.get_edge_data(src, node)
                    inputs[src] = edge_data.get('value', 0)
            
            # Get output addresses and values
            outputs = {}
            for _, dst in graph.out_edges(node):
                if graph.nodes[dst].get('type') == 'address':
                    edge_data = graph.get_edge_data(node, dst)
                    outputs[dst] = edge_data.get('value', 0)
            
            # Create direct connections from inputs to outputs
            for input_addr, input_val in inputs.items():
                for output_addr, output_val in outputs.items():
                    if input_addr != output_addr:  # Avoid self-loops
                        # Calculate proportional value transfer
                        total_input = sum(inputs.values())
                        if total_input > 0:
                            # Value transferred from input_addr to output_addr through this tx
                            transfer_value = (input_val / total_input) * output_val
                            
                            if transfer_value >= min_value:
                                # Add or update the edge
                                if simplified_graph.has_edge(input_addr, output_addr):
                                    # Sum the values if edge already exists
                                    current_value = simplified_graph[input_addr][output_addr]['value']
                                    simplified_graph[input_addr][output_addr]['value'] = current_value + transfer_value
                                else:
                                    # Create new edge
                                    simplified_graph.add_edge(
                                        input_addr,
                                        output_addr,
                                        value=transfer_value,
                                        tx_hash=node
                                    )
        
        # Find paths from source to targets
        paths = []
        
        if target_addresses:
            for target in target_addresses:
                if target in simplified_graph:
                    try:
                        # Find all simple paths from source to target
                        for path in nx.all_simple_paths(simplified_graph, source_address, target, cutoff=10):
                            # Calculate total value transferred along the path
                            path_value = float('inf')
                            for i in range(len(path) - 1):
                                edge_value = simplified_graph[path[i]][path[i+1]]['value']
                                path_value = min(path_value, edge_value)
                            
                            paths.append({
                                'path': path,
                                'value': path_value,
                                'length': len(path) - 1  # Number of hops
                            })
                    except nx.NetworkXNoPath:
                        continue
        else:
            # Find paths to all possible targets
            for target in simplified_graph.nodes():
                if target != source_address:
                    try:
                        # Find shortest path first (up to a cutoff to avoid too long paths)
                        for path in nx.all_simple_paths(simplified_graph, source_address, target, cutoff=5):
                            # Calculate minimum value transferred along the path
                            path_value = float('inf')
                            for i in range(len(path) - 1):
                                edge_value = simplified_graph[path[i]][path[i+1]]['value']
                                path_value = min(path_value, edge_value)
                            
                            if path_value >= min_value:
                                paths.append({
                                    'path': path,
                                    'value': path_value,
                                    'length': len(path) - 1  # Number of hops
                                })
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        continue
        
        # Sort paths by value (descending)
        paths.sort(key=lambda x: x['value'], reverse=True)
        return paths 