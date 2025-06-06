import Obfuscation
import requests
from web3 import Web3
import json
from openai import OpenAI
from evmdasm import EvmBytecode
import subprocess
client = OpenAI()
RPC_URL = "http://127.0.0.1:8545" 
LOG_FILE = "results.log"  
def process_fifth_feature(ssa, contract_address,bytecode,PRIVATE_KEY):
    results = []
    log_found = False
    # can_send, functions_that_can_send = ssa.can_send_ether()
    for function in sorted(ssa.functions, key=lambda f: f.offset):
        for block in function:
            for insn in block:
                if insn.insn.name == 'SELFDESTRUCT':
                    address = insn.arguments[0]
                elif insn.insn.name == 'CALL':
                   
                    current_block = insn.parent_block
                
                    cfg = Obfuscation.ControlFlowGraph(function)
                    predecessors = find_predecessors_by_offset(function, current_block.offset)
                    seen_logs = set()  
                    for block in predecessors:
                        for inst in block:
                            if inst.insn.name.startswith("LOG"): 
                                log_key = (block.offset, inst.insn) 
                                if log_key not in seen_logs: 
                                    seen_logs.add(log_key)  
                                    log_found = True
                    

                    results.append({
                        "function": function.desc(),
                        "call_instruction": f"Block {current_block.offset:#x}",
                        "log_found": log_found,
                    })
    print(f"(8)log_found: {log_found}")
    return log_found
    # if(log_found):
    #     evm_bytecode = EvmBytecode(bytecode)
    #     disassembly = evm_bytecode.disassemble()

    #     def extract_call_related_selectors(disassembly):

    #         selectors = []  
    #         call_indices = []  

    #         for idx, instr in enumerate(disassembly):
    #             if instr.name == "PUSH4":
    #                 selectors.append(instr.operand) 
    #             elif instr.name == "CALL":
    #                 call_indices.append(len(selectors) - 1) 


    #         result = set() 
    #         for call_idx in call_indices:
    #             if call_idx >= 0: 
    #                 result.add(selectors[call_idx]) 
    #                 if call_idx > 0:
    #                     result.add(selectors[call_idx - 1])  
    #                 if call_idx < len(selectors) - 1:
    #                     result.add(selectors[call_idx + 1])  

    #         return list(result) 


    #     call_related_selectors = extract_call_related_selectors(disassembly)


    #     print("与 Transfer 相关的函数选择器：")
    #     for idx, selector in enumerate(call_related_selectors, start=1):
    #         print(f"{idx}: {selector}")

            
    #     for selector in call_related_selectors:
    #         try:
    #             # 构造 cast send 命令
    #             command = [
    #                             "cast", "send", contract_address, f"0x{selector}",
    #                             "--rpc-url", RPC_URL,
    #                             "--private-key", PRIVATE_KEY,
    #                             "--gas-limit", "100000"
    #                     ]

    #             result = subprocess.run(command, capture_output=True, text=True)
    #             if result.returncode == 0:
    #                 with open(LOG_FILE, "a") as log:
    #                     log.write(f"Selector {selector}: SUCCESS\n{result.stdout}\n")
    #                 print(f"Selector {selector}: SUCCESS")
    #             else:
    #                 with open(LOG_FILE, "a") as log:
    #                     log.write(f"Selector {selector}: FAILED\n{result.stderr}\n")
    #                 print(f"Selector {selector}: FAILED")
    #         except Exception as e:
    #             print(f"Error calling selector {selector}: {e}")

    #     LOCAL_RPC_URL = "http://127.0.0.1:8545"  # 本地运行的以太坊节点
    #     web3 = Web3(Web3.HTTPProvider(LOCAL_RPC_URL))

    #     if not web3.is_connected():
    #         print("Failed to connect to local Ethereum network.")
    #         exit()
    #     else:
    #         print("Connected to local Ethereum network.")

    #     # 定义合约地址和 ABI
    #     contract_address = Web3.to_checksum_address(contract_address)

    #     contract_abi = [
    #         {
    #             "anonymous": False,
    #             "inputs": [],
    #             "name": "PlaceholderEvent",
    #             "type": "event",
    #         }
    #     ]
    #     from_block = 0  
    #     to_block = "latest"  
    #     try:
    #         logs = web3.eth.get_logs({
    #             "fromBlock": from_block,
    #             "toBlock": to_block,
    #             "address": contract_address,
    #         })

    #         print(f"Found {len(logs)} logs.")

    #         for log in logs:
    #             if log['data'] and log['data'] != "0x":
    #                 try:
    #                     print(f"Data: {log['data']}")
    #                 except Exception as decode_error:
    #                     print(f"Error processing data from log: {decode_error}")
    #             else:
    #                 print("Log does not contain data or data is empty, skipping.")

    #     except Exception as e:
    #         print(f"Error while fetching logs: {e}")
        
    #     def analyze_log_data(data):
    #         prompt = f"""
    #         The following data is emitted from a smart contract's log. Analyze it to find any readable sentences. 
    #         If a readable sentence is found, determine whether it implies a "direct transfer" action.
            
    #         Data: {data}
            
    #         Output format:
    #         - Extracted sentence(s): [The readable sentence(s)]
    #         - Direct transfer semantics: 0 (No) or 1 (Yes)
    #         """
    #         completion = client.chat.completions.create(
    #             model="gpt-3.5-turbo-0125",
    #             messages=[
    #                 {"role": "system", "content": "You are a helpful assistant."},
    #                 {
    #                     "role": "user",
    #                     "content": prompt
    #                 }
    #             ]
    #         )
    #         return completion.choices[0].message

    #     for log in logs:
    #         result = analyze_log_data(log['data'])

    #         print("Semantic Analysis Result:")
    #         # 提取 "Extracted sentence(s)" 的内容
    #         extracted_sentence = result.content.split("- Extracted sentence(s):", 1)[-1].split("- Direct transfer semantics:")[0].strip()
    #         direct_transfer_semantics = result.content.split("- Direct transfer semantics:", 1)[-1].strip()

    #         print(f"Extracted sentence: {extracted_sentence}")
    #         print(f"Direct transfer semantics: {direct_transfer_semantics}")
    print("-----------------------------------------------------------")





def find_predecessors_by_offset(function, current_offset, max_blocks=50):

    blocks = sorted(function, key=lambda b: b.offset)
    predecessor_blocks = []

    for block in blocks:
        if block.offset >= current_offset:
            break
        predecessor_blocks.append(block)

    return predecessor_blocks[-max_blocks:]

def get_predecessor_blocks(cfg, block, depth):

    predecessors = []
    queue = [(block, 0)] 
    visited = set()

    while queue:
        current_block, current_depth = queue.pop(0)

        if current_block in visited:
            continue
        visited.add(current_block)

        if current_depth == depth:
            break


        preds = [pred for pred, succ in cfg.edges if succ == current_block]
        predecessors.extend(preds)


        for pred in preds:
            queue.append((pred, current_depth + 1))

    return predecessors[:depth]  
