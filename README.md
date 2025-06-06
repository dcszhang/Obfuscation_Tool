# Obfuscation_Tool

## Introduction

**Obfuscation_Tool** is a Python-based framework for analyzing and quantifying obfuscation in Ethereum smart contract bytecode. This repository implements the methods described in the paper “Obfuscation Unmasked: Revealing Hidden Logic in Ethereum Scam Contracts via Bytecode-Level Transfer Analysis.” The tool extracts seven bytecode-level obfuscation features (F1–F7) from smart contracts, computes a Z-score for each contract, and outputs detailed per-contract metrics.

Key capabilities include:

- **Single-contract analysis**: Parse a raw bytecode string and extract F1–F7 as defined in the paper:
  1. **F1. Number of steps in address generation**  
     Backward dataflow analysis on the `address` variable, counting distinct arithmetic, hash, bitwise, and external-call steps.
  2. **F2. Number of string operations**  
     Count of all string-manipulation and hash instructions involved in `address` generation.
  3. **F3. Presence of external call**  
     Binary flag indicating whether any `CALL`, `DELEGATECALL`, or `STATICCALL` appears in the `addr`/`value` dataflow.
  4. **F4. Height of branch tree**  
     Maximum nesting depth of conditional branches (`JUMPI`) along the transfer’s control-flow path.
  5. **F5. Transfer-related instruction ratio (TIR)**  
     Ratio of effective transfer- and state-update instructions to total instructions in the transfer-residing function.
  6. **F6. Transfer operation similarity**  
     Cosine similarity between R-GCN–embedded PDG representations of transfer-containing functions.
  7. **F7. Relevance of log events**  
     Binary flag indicating whether logs emitted within two CFG hops of a transfer are semantically relevant.
- **Batch analysis (multi-threaded)**: Use Dask to process a CSV of bytecode strings in parallel and store all per-contract results (F1–F7 and Z-score) in `output.csv`.
- **Reproducibility**: Includes scripts for training Word2Vec embeddings (`word2vec_Train/`) and for running on a Dask cluster.

---


- **rattle-cli.py**: The single‐contract CLI entrypoint. Reads a raw bytecode string from STDIN (no extension), invokes the analysis pipeline, and prints a human‐readable report plus a final numeric summary (as a list of values).  

- **rundask.py**: The batch‐mode script. It expects a CSV file with columns:
```

bytecode,address
\<hex string without 0x>,<contract address>
```
Modify the `csv_path` variable near the top of `rundask.py` to point to your CSV (e.g., `test.csv`). Then run with:
```
python rundask.py
````
This will:
1. Spin up a local Dask cluster.  
2. Partition the dataset (by default, from 1 to 10 partitions).  
3. Dispatch each partition to a worker, run the same analysis pipeline as `rattle-cli.py`, collect results.  
4. Save all per‐contract metrics into `output.csv` in the repository root.  
5. Print progress messages like:
   ```
   Dashboard: http://127.0.0.1:8787/status
   Initial partitions: 1
   Final partitions: 10
   ✅ Process 0 completed: ...
   …
   ✅ All tasks finished! Saved to output.csv
   ```

---

## Installation

1. **Clone the repository**:
 ```bash
 git clone https://github.com/dcszhang/Obfuscation_Tool.git
 cd Obfuscation_Tool
````

2. **Set up a Python 3.10+ environment** (recommended: use `venv` or `conda`):

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux
   # OR
   # venv\Scripts\activate     # Windows PowerShell
   ```

3. **Install required packages**. 
Run:

   ```bash
   pip install \
       dask[complete] \
       pandas \
       numpy \
       networkx \
       scikit‐learn \
       gensim \
       pyparsing \
       tqdm
   ```

   Adjust versions as needed. For GPU‐accelerated experiments (RGCN, t‐SNE with CUDA), install the appropriate CUDA‐enabled libraries.

---

## Usage

### 1. Single‐Contract Analysis

This mode is useful when you have a single raw bytecode string (no file extension). For example:

```bash
# Suppose you have a file `example_bytecode.txt` containing:
# 608060405234801561001057600080fd5b506040516101003803806101008339818101604052
# You can run:
python rattle-cli.py < example_bytecode.txt
```

Prints a formatted report, for example:

   ```
   --------------------------------------------------------------------------------------
                            Smart contract analysis process
   --------------------------------------------------------------------------------------
   This is the 1 transfer
       (1) Found Transfer Address instruction:
               %145 = AND(%144, #4c36d2919e407f0cc2ee3c993ccf8ac26d9ce64e)
       (2) trace_step: 3
       (3) Tree height: 4
       (4) String Operation times: 0
   -----------------------------------------------------------
   This is the 2 transfer
       …
   
   --------------------------------------------------------------------------------------
                                     END
   --------------------------------------------------------------------------------------
   [3, 4, 0, 99.6111512184143, False, 0.5784313725490197, False]
   ```
---

### 2. Batch Analysis (Multi‐Threaded via Dask)

When you have many contracts to analyze, you can process them in parallel:

1. **Prepare a CSV** (`test.csv` or your own) with **two columns** and a header row:

   ```csv
   bytecode,address
   6080604052348015610010...,0xAbCdEf123...
   60806040526004361...,0xDeFaCe456...
   …
   ```

   * `bytecode`: Hex string (no `0x` prefix, no file extension) per row.
   * `address`: Contract address or identifier (used for labeling output).

2. **Edit `rundask.py`**:

   * Open `rundask.py` in a text editor.
   * Modify the `csv_path` variable (near the top) to point to your CSV file. For example:

     ```python
     csv_path = "test.csv"
     ```

3. **Run the batch script**:

   ```bash
   python rundask.py
   ```

   You will see output like:

   ```
   Dashboard: http://127.0.0.1:8787/status
   Initial partitions: 1
   Final partitions: 10
   ✅ Process 0 completed: <contract_address_1>
   ✅ Process 1 completed: <contract_address_2>
   ✅ Process 2 completed: <contract_address_3>
   …
   ✅ All tasks finished! Saved to output.csv
   ```

   * A Dask dashboard will be available at `http://127.0.0.1:8787/status` (open in browser to monitor real‐time progress).
   * The script automatically repartitions the dataset (default: from 1 to 10 partitions) and distributes tasks across available CPU cores.
   * Once all partitions are processed, a single file `output.csv` will be created in the repository root.
---

<!-- ## Citation

If you use **Obfuscation\_Tool** in your research, please cite the associated paper:

```
@inproceedings{zhang2025obfuscation,
  title={Obfuscation Unmasked: Revealing Hidden Logic in Ethereum Scam Contracts via Bytecode‐Level Transfer Analysis},
  author={Zhang, Sheng and [Other Authors]},
  booktitle={Proceedings of the CCS Security Conference 2025},
  year={2025},
  pages={XX--XX},
}
``` -->

---

## Contributing

Contributions are welcome! If you find a bug or want to add a new feature (e.g., additional obfuscation metrics, support for alternative EVM versions), please:

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/YourFeature`).
3. Make your changes, ensuring all existing tests pass.
4. Submit a Pull Request with a clear description of your changes.

Please follow PEP 8 style guidelines and add appropriate documentation or unit tests for new modules.

---

## License

This project is released under the **MIT License**. See `LICENSE` for details.

---

