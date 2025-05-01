"""
Graph visualization module.

This module provides functionality for visualizing blockchain transaction graphs.
"""

import logging
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class TransactionGraphVisualizer:
    """
    Visualizes blockchain transaction graphs using various methods.
    """
    
    def __init__(self, transaction_graph=None):
        """
        Initialize the transaction graph visualizer.
        
        Args:
            transaction_graph (networkx.DiGraph, optional): The transaction graph to visualize.
        """
        self.graph = transaction_graph or nx.DiGraph()
        
        # Color schemes
        self.address_color = '#1f77b4'  # blue
        self.target_address_color = '#d62728'  # red
        self.transaction_color = '#2ca02c'  # green
        self.edge_color = '#7f7f7f'  # gray
        
    def set_graph(self, graph):
        """
        Set the transaction graph to visualize.
        
        Args:
            graph (networkx.DiGraph): The transaction graph.
        """
        self.graph = graph
    
    def visualize_matplotlib(self, output_path=None, figsize=(16, 12)):
        """
        Visualize the transaction graph using matplotlib.
        
        Args:
            output_path (str, optional): The file path to save the visualization. 
                                        If None, the plot is displayed interactively.
            figsize (tuple, optional): The figure size (width, height) in inches.
            
        Returns:
            matplotlib.figure.Figure: The figure object.
        """
        if not self.graph:
            logger.warning("No graph to visualize.")
            return None
        
        # Create the figure
        plt.figure(figsize=figsize)
        
        # Get node positions using a force-directed layout
        pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        
        # Separate nodes by type
        address_nodes = [n for n, d in self.graph.nodes(data=True) 
                          if d.get('type') == 'address' and not d.get('is_target')]
        target_nodes = [n for n, d in self.graph.nodes(data=True) 
                          if d.get('type') == 'address' and d.get('is_target')]
        transaction_nodes = [n for n, d in self.graph.nodes(data=True) 
                              if d.get('type') == 'transaction']
        
        # Draw nodes by type
        nx.draw_networkx_nodes(self.graph, pos, 
                              nodelist=address_nodes,
                              node_color=self.address_color,
                              node_size=300,
                              alpha=0.8,
                              label='Addresses')
                              
        nx.draw_networkx_nodes(self.graph, pos, 
                              nodelist=target_nodes,
                              node_color=self.target_address_color,
                              node_size=500,
                              alpha=0.8,
                              label='Target Address')
                              
        nx.draw_networkx_nodes(self.graph, pos, 
                              nodelist=transaction_nodes,
                              node_color=self.transaction_color,
                              node_size=200,
                              alpha=0.8,
                              node_shape='s',
                              label='Transactions')
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, 
                              edge_color=self.edge_color,
                              width=1.0,
                              alpha=0.5,
                              arrows=True,
                              arrowsize=10)
        
        # Add labels to target nodes only (to avoid cluttering)
        labels = {n: n[:8] + '...' if len(n) > 10 else n 
                  for n in target_nodes}
        nx.draw_networkx_labels(self.graph, pos, 
                               labels=labels,
                               font_size=10,
                               font_color='black')
        
        plt.title("Blockchain Transaction Graph", fontsize=16)
        plt.legend(scatterpoints=1)
        plt.axis('off')
        
        # Save or display the plot
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            logger.info(f"Visualization saved to {output_path}")
        else:
            plt.tight_layout()
            plt.show()
            
        return plt.gcf()
    
    def visualize_plotly(self, output_path=None, height=800, width=1200):
        """
        Visualize the transaction graph using Plotly for interactive visualization.
        
        Args:
            output_path (str, optional): The file path to save the visualization HTML.
                                        If None, the plot is returned as a Plotly figure.
            height (int, optional): The figure height in pixels.
            width (int, optional): The figure width in pixels.
            
        Returns:
            plotly.graph_objects.Figure: The Plotly figure object.
        """
        if not self.graph:
            logger.warning("No graph to visualize.")
            return None
        
        # Get node positions using a force-directed layout
        pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        
        # Prepare node data
        node_x = []
        node_y = []
        node_color = []
        node_size = []
        node_text = []
        node_symbol = []
        
        for node, attrs in self.graph.nodes(data=True):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Set node color and size based on type
            if attrs.get('type') == 'transaction':
                node_color.append(self.transaction_color)
                node_size.append(10)
                node_symbol.append('square')
                
                # Create label with transaction details
                timestamp = attrs.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, datetime):
                        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_str = str(timestamp)
                else:
                    time_str = "Unknown"
                    
                value = attrs.get('value', 0)
                tx_label = f"Transaction: {node[:8]}...<br>Value: {value}<br>Time: {time_str}"
                node_text.append(tx_label)
                
            elif attrs.get('type') == 'address':
                if attrs.get('is_target'):
                    node_color.append(self.target_address_color)
                    node_size.append(20)
                else:
                    node_color.append(self.address_color)
                    node_size.append(15)
                    
                node_symbol.append('circle')
                node_text.append(f"Address: {node[:10]}..." if len(node) > 10 else f"Address: {node}")
        
        # Prepare edge data
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in self.graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Add a midpoint with a slight offset for the arc
            # This creates a curved edge for better visualization
            if x0 != x1 and y0 != y1:
                # Calculate perpendicular direction for curve
                dx = x1 - x0
                dy = y1 - y0
                dist = np.sqrt(dx*dx + dy*dy)
                dx, dy = dx/dist, dy/dist
                
                # Perpendicular vector
                px, py = -dy, dx
                
                # Midpoint with offset
                xm = (x0 + x1) / 2 + px * dist * 0.2
                ym = (y0 + y1) / 2 + py * dist * 0.2
                
                # Create the curved path
                edge_x.extend([x0, xm, x1, None])
                edge_y.extend([y0, ym, y1, None])
            else:
                # Straight line if points align perfectly
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            # Edge tooltip
            edge_type = edge[2].get('type', 'unknown')
            edge_value = edge[2].get('value', 0)
            edge_text.append(f"Type: {edge_type}<br>Value: {edge_value}")
        
        # Create the figure
        fig = make_subplots(rows=1, cols=1)
        
        # Add edges
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.7, color='#7f7f7f'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        fig.add_trace(edge_trace)
        
        # Add nodes
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color,
                symbol=node_symbol,
                line=dict(width=1, color='#000000')
            ),
            text=node_text,
            hoverinfo='text'
        )
        fig.add_trace(node_trace)
        
        # Update layout
        fig.update_layout(
            title='Blockchain Transaction Graph',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=height,
            width=width,
            template='plotly_white'
        )
        
        # Save or return the figure
        if output_path:
            fig.write_html(output_path)
            logger.info(f"Interactive visualization saved to {output_path}")
            
        return fig
    
    def create_dashboard(self, analysis_results=None, output_path=None):
        """
        Create an interactive dashboard with the graph visualization and transaction analysis.
        
        Args:
            analysis_results (dict, optional): Dictionary containing analysis results.
            output_path (str, optional): Path to save the dashboard HTML file.
            
        Returns:
            dash.Dash: The Dash app object.
        """
        # This function would create a Dash app with multiple interactive components
        # Including transaction graph, metrics, path analysis, etc.
        # Implementation requires dash, which would be better done in a separate file
        
        logger.info("Dashboard creation requires a separate implementation using Dash.")
        logger.info("See documentation for instructions on creating a full dashboard.")
        
        # Return the Plotly figure as a basic alternative
        return self.visualize_plotly(output_path)
    
    def export_graph_data(self, output_path=None, format='csv'):
        """
        Export the graph data to a file format for further analysis.
        
        Args:
            output_path (str, optional): Path to save the exported data.
            format (str, optional): Export format ('csv', 'graphml', 'gexf').
            
        Returns:
            dict: Dictionary with node and edge DataFrames if format is 'csv'.
        """
        if not self.graph:
            logger.warning("No graph to export.")
            return None
        
        if format.lower() == 'csv':
            # Convert to pandas DataFrames
            node_data = []
            for node, attrs in self.graph.nodes(data=True):
                node_info = {'id': node}
                node_info.update(attrs)
                node_data.append(node_info)
                
            edge_data = []
            for source, target, attrs in self.graph.edges(data=True):
                edge_info = {'source': source, 'target': target}
                edge_info.update(attrs)
                edge_data.append(edge_info)
                
            nodes_df = pd.DataFrame(node_data)
            edges_df = pd.DataFrame(edge_data)
            
            if output_path:
                # Save to separate CSV files
                nodes_path = f"{output_path}_nodes.csv" if not output_path.endswith('.csv') else output_path.replace('.csv', '_nodes.csv')
                edges_path = f"{output_path}_edges.csv" if not output_path.endswith('.csv') else output_path.replace('.csv', '_edges.csv')
                
                nodes_df.to_csv(nodes_path, index=False)
                edges_df.to_csv(edges_path, index=False)
                
                logger.info(f"Nodes exported to {nodes_path}")
                logger.info(f"Edges exported to {edges_path}")
                
            return {'nodes': nodes_df, 'edges': edges_df}
            
        elif format.lower() in ['graphml', 'gexf']:
            if not output_path:
                output_path = f"transaction_graph.{format.lower()}"
                
            if format.lower() == 'graphml':
                nx.write_graphml(self.graph, output_path)
            else:  # gexf
                nx.write_gexf(self.graph, output_path)
                
            logger.info(f"Graph exported to {output_path} in {format.upper()} format")
            return output_path
            
        else:
            logger.error(f"Unsupported export format: {format}")
            return None 