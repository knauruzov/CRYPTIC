# DFIR CRYPTIC (Crypto-Forensic Research & Yielded Transaction Intelligence Core)

## Project Goals

The primary objectives of the DFIR CRYPTIC project are to provide comprehensive tools and methodologies for cryptocurrency forensic analysis. This involves several key areas:

1.  **De-anonymization:** Establishing connections between blockchain addresses and real-world entities.
    *   **Methodologies:** Utilize clustering algorithms based on transaction history (e.g., common-input-ownership heuristic), analyze metadata associated with transactions, correlate blockchain activity with off-chain data sources (social media, forums, breached databases, KYC information from compliant exchanges through legal channels), and leverage advanced OSINT techniques.
    *   **Challenges:** Overcoming privacy-enhancing technologies (e.g., CoinJoin, privacy coins like Monero), dealing with pseudonymous identities used across multiple platforms, navigating jurisdictional limitations for accessing exchange data.
    *   **Outcome:** A robust framework capable of suggesting potential identities linked to addresses of interest with quantifiable confidence scores.

2.  **Transaction Tracking:** Following the movement of funds across the blockchain network.
    *   **Methodologies:** Implement graph traversal algorithms (e.g., Breadth-First Search, Depth-First Search) on the blockchain transaction graph, develop techniques for tracing funds through mixers and tumblers (e.g., timing analysis, volume analysis, taint analysis), and identify intermediary wallets used for obfuscation.
    *   **Challenges:** Handling the sheer volume and complexity of blockchain data, identifying and bypassing sophisticated obfuscation techniques, tracking cross-chain transactions and atomic swaps.
    *   **Outcome:** A system that can trace cryptocurrency flows from source to destination, identifying key intermediary hops and potential cash-out points.

3.  **Suspicious Pattern Identification:** Detecting illicit activities through transaction analysis.
    *   **Methodologies:** Develop rule-based systems based on known money laundering typologies (e.g., structuring, layering), apply anomaly detection algorithms and machine learning models (supervised and unsupervised) to identify deviations from normal transaction behavior, flag interactions with addresses associated with known illicit activities (darknet markets, ransomware operators, sanctioned entities).
    *   **Challenges:** Minimizing false positives, adapting to evolving criminal tactics, obtaining reliable ground truth data for training machine learning models, addressing the "unknown unknowns" in illicit finance.
    *   **Outcome:** An early warning system that flags potentially suspicious transactions and wallets for further investigation, prioritizing alerts based on risk scoring.

4.  **Transaction Visualization:** Providing clear and actionable insights through visual representation.
    *   **Methodologies:** Utilize graph visualization libraries (e.g., Gephi, Cytoscape.js, NetworkX) to create interactive and customizable representations of transaction networks, implement features for filtering, highlighting, and exploring transaction paths, develop temporal analysis visualizations to understand the timing of fund movements.
    *   **Challenges:** Rendering large and complex graphs efficiently, designing intuitive interfaces for non-technical users, ensuring visualizations accurately reflect the underlying data without oversimplification.
    *   **Outcome:** An interactive dashboard enabling analysts to visually explore transaction histories, understand fund flows, identify key actors, and effectively communicate findings.

## Installation

### Prerequisites

- Python 3.9 or higher
- Git (for cloning the repository)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/dfir-cryptic.git
   cd dfir-cryptic
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up API keys:
   
   Create a `.env` file in the root directory with the following content:
   ```
   BLOCKCYPHER_API_KEY=your_blockcypher_api_key
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```
   
   You can obtain these API keys by registering at:
   - [BlockCypher](https://www.blockcypher.com/)
   - [Etherscan](https://etherscan.io/apis)

## Usage

DFIR CRYPTIC provides a command-line interface to perform various cryptocurrency forensic tasks.

### General Help

```
python main.py -h
```

### Available Commands

#### 1. Address Information

Get detailed information about a blockchain address:

```
python main.py address <ADDRESS> --blockchain <BLOCKCHAIN>
```

Example:
```
python main.py address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc
```

Parameters:
- `<ADDRESS>`: The blockchain address to analyze
- `--blockchain` or `-b`: Blockchain to analyze (`btc` or `eth`, default: `btc`)

#### 2. Transaction Information

Get detailed information about a specific transaction:

```
python main.py transaction <TX_HASH> --blockchain <BLOCKCHAIN>
```

Example:
```
python main.py transaction a7be9a08610337dd43f04b9c04bf8c27eb9ec13fdd12e128861be10874993f19 -b btc
```

Parameters:
- `<TX_HASH>`: The transaction hash to analyze
- `--blockchain` or `-b`: Blockchain to analyze (`btc` or `eth`, default: `btc`)

#### 3. Transaction Graph Analysis

Create and visualize a transaction graph for a given address:

```
python main.py graph <ADDRESS> --blockchain <BLOCKCHAIN> --depth <DEPTH> --max-addresses <MAX_ADDRESSES> --format <FORMAT> --output <OUTPUT_FILE>
```

Example:
```
python main.py graph 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc --depth 2 --format html
```

Parameters:
- `<ADDRESS>`: The starting address for graph analysis
- `--blockchain` or `-b`: Blockchain to analyze (`btc` or `eth`, default: `btc`)
- `--depth` or `-d`: Depth of transaction graph (default: 2)
- `--max-addresses` or `-m`: Maximum number of addresses to include (default: 100)
- `--format` or `-f`: Output format (`png`, `html`, `csv`, `graphml`, default: `html`)
- `--output` or `-o`: Output file path (optional)

#### 4. Fund Tracing

Trace funds from a source address to target addresses:

```
python main.py trace <SOURCE_ADDRESS> [TARGET_ADDRESSES...] --blockchain <BLOCKCHAIN> --depth <DEPTH> --min-value <MIN_VALUE> --output <OUTPUT_FILE>
```

Example:
```
python main.py trace bc1p6weafx7e2s5agl58cr99wruut4xktmuwa56jwzgymqhx9u5ln67sj404t5 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc --depth 3
```

Parameters:
- `<SOURCE_ADDRESS>`: The source address to trace funds from
- `[TARGET_ADDRESSES...]`: Optional target addresses to trace to
- `--blockchain` or `-b`: Blockchain to analyze (`btc` or `eth`, default: `btc`)
- `--depth` or `-d`: Depth of transaction graph (default: 3)
- `--min-value`: Minimum value to consider for tracing (default: 0)
- `--output` or `-o`: Output file for saving results (optional)

#### 5. Mixer Detection

Detect potential cryptocurrency mixers:

```
python main.py mixers --address <ADDRESS> --blockchain <BLOCKCHAIN> --input-graph <GRAPH_FILE> --output <OUTPUT_FILE>
```

Example:
```
python main.py mixers --address bc1p6weafx7e2s5agl58cr99wruut4xktmuwa56jwzgymqhx9u5ln67sj404t5 -b btc
```

Parameters:
- `--address` or `-a`: Starting address for analysis (optional)
- `--blockchain` or `-b`: Blockchain to analyze (`btc` or `eth`, default: `btc`)
- `--input-graph` or `-i`: Input graph file from previous analysis (optional)
- `--output` or `-o`: Output file for saving results (optional)

Note: Either `--address` or `--input-graph` must be specified.

### Additional Options

- `--verbose` or `-v`: Enable verbose output with detailed logging

## Output Data

The tool can output data in various formats:
- Transaction graphs: PNG images, interactive HTML, CSV files, or GraphML files
- Analysis results: JSON files

## Examples

### Example 1: Basic Address Information

```
python main.py address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc
```

This will display information about the Bitcoin genesis address, including balance and recent transactions.

### Example 2: Tracing Funds Between Addresses

```
python main.py trace bc1p6weafx7e2s5agl58cr99wruut4xktmuwa56jwzgymqhx9u5ln67sj404t5 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc --depth 1
```

This will trace funds from the source address to the target address (in this case, the Bitcoin genesis address).

### Example 3: Generate Interactive Transaction Graph

```
python main.py graph 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa -b btc --depth 1 --format html --output genesis_transactions.html
```

This will create an interactive HTML visualization of transactions related to the Bitcoin genesis address. 