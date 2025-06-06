# Obfuscation_Tool

## Introduction

**Obfuscation_Tool** is a Python-based framework for analyzing and quantifying obfuscation in Ethereum smart contract bytecode. This repository contains the implementation of the methods described in the paper [“Obfuscation Unmasked: Revealing Hidden Logic in Ethereum Scam Contracts via Bytecode-level Transfer Analysis”]. The tool extracts a set of obfuscation-related features from one or more smart contracts, computes a Z‐score ranking to identify heavily obfuscated contracts, and outputs detailed per-contract metrics.

Key capabilities include:

- **Single‐contract analysis**: Parse a raw bytecode string and report:
  1. Transfer‐graph metrics (trace depth, control‐flow tree height, string‐operation count).
  2. Maximum similarity between transfer subgraphs.
  3. Presence of external‐call conditions guarding transfers.
  4. Function‐level instruction statistics (call‐related vs. “useless” instructions, related‐ratio).
  5. PHI‐node occurrences and transfer‐address traces.
- **Batch analysis (multi‐threaded)**: Use Dask to process a large CSV of bytecode strings in parallel and store all per‐contract results in `output.csv`.
- **Reproducibility**: Includes scripts for training Word2Vec embeddings (`word2vec_Train/`) and for running on a Dask cluster.

---

## Repository Structure

```

Obfuscation\_Tool/
├── Obfuscation/
│   ├── **init**.py
│   ├── analyze.py
│   ├── condition.py
│   ├── evmasm.py
│   ├── feature1.py
│   ├── feature2.py
│   ├── feature3.py
│   ├── feature4.py
│   ├── feature5.py
│   ├── hashes.py
│   ├── main.py
│   ├── recover.py
│   ├── rgcn.py
│   ├── ssa.py
│   ├── tsne.py
│   └── **pycache**/  (compiled .pyc files)
├── bytecode/                     ← (Optional) Sample bytecode files (hex strings without .txt)
├── word2vec\_Train/
│   ├── cfg.model                ← Configuration for Word2Vec training
│   ├── trainword2vec.py         ← Script to train word2vec embeddings on extracted operation sequences
│   └── word2vec.model           ← Pretrained Word2Vec model (optional)
├── rattle-cli.py                ← Command‐line interface for single‐contract analysis
├── rundask.py                   ← Script to run batch analysis over a CSV via Dask
├── README.md                    ← (This file)
├── output.csv                   ← (Generated) Consolidated results after batch run
├── single\_output.txt            ← (Generated) Raw single‐contract output example
├── test.csv                     ← (Example) CSV 
└── template with `bytecode,address` columns for batch mode
```

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
 git clone https://github.com/<your‐username>/Obfuscation_Tool.git
 cd Obfuscation_Tool
````

2. **Set up a Python 3.10+ environment** (recommended: use `venv` or `conda`):

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux
   # OR
   # venv\Scripts\activate     # Windows PowerShell
   ```

3. **Install required packages**. If `obfuscation_tool_requirements.txt` is provided, run:

   ```bash
   pip install -r obfuscation_tool_requirements.txt
   ```

   Otherwise, install at least:

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
   -----------------------------------------------------------
   (5) The maximum similarity between graphs:
       Graph 0 and Graph 2: 99.6112%
   -----------------------------------------------------------
   (6) Address and Value in Transfer(External Call): False
   -----------------------------------------------------------
   (7) Function: _unknown_0xc19e1aea()
       Total instructions: 102
       call_related_instructions: 59
       SSTORE_related_instructions: 0
       Total Useless instructions: 43
       Related Ratio: 57.84%
   -----------------------------------------------------------
   (7) Function: execute(bytes)
       …
   -----------------------------------------------------------
   The function with the lowest Related Ratio:
   Function: _unknown_0xc19e1aea()
       Related Ratio: 57.84%
   -----------------------------------------------------------
   (8) log_found: False
   Found PHI node: %240 = EQ(%238, #0)
   Transfer Address Trace:
   …
   (9) Transfer have an external call condition to execute: False
   --------------------------------------------------------------------------------------
                                     END
   --------------------------------------------------------------------------------------
   [3, 4, 0, 99.6111512184143, False, 0.5784313725490197, False, False]
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

