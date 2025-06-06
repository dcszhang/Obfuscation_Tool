
import Obfuscation
import os
import tempfile
def process_fourth_feature(ssa, threshold=0.1):

    instruction_sequences = {}
    for function in sorted(ssa.functions, key=lambda f: f.offset):
        instruction_sequences[function] = sum(len(block) for block in function)


    sdg = Obfuscation.SystemDependenceGraph(ssa.functions)

    call_backtracking = Obfuscation.CallBacktracking(sdg)

    lowest_ratio = float('inf')
    lowest_ratio_func = None

    for func, paths in call_backtracking.get_backtrack_results().items():
        if not paths:
            continue

        function_total_instructions = instruction_sequences[func] 
        call_related_instructions = set()
        for path in paths:
            call_related_instructions.update(
                {insn for block in path for insn in block}
            )

        if len(call_related_instructions) == 0:
            continue


        all_instructions = {insn for block in func for insn in block}


        remaining_instructions = all_instructions - call_related_instructions

        before_sstore_instructions = remaining_instructions.copy()

        result_original = process_sstore_recursive_analysis(ssa, remaining_instructions)
        result = result_original[0]
        remaining_instructions_after_sstore = result["remaining_instructions"]

        sstore_instructions = before_sstore_instructions - remaining_instructions_after_sstore


        final_useless_instructions = remaining_instructions_after_sstore

        total_related_instructions = len(all_instructions) - len(final_useless_instructions)
        ratio = total_related_instructions / len(all_instructions)

        if ratio < lowest_ratio:
            lowest_ratio = ratio
            lowest_ratio_func = func

        print(f"(7)Function: {func.desc()}")
        print(f"    Total instructions: {len(all_instructions)}")
        print(f"    call_related_instructions: {len(call_related_instructions)}")
        print(f"    SSTORE_related_instructions: {len(sstore_instructions)}")
        print(f"    Total Useless instructions: {len(final_useless_instructions)}")
        print(f"    Related Ratio: {ratio:.2%}")
        print("-----------------------------------------------------------")

    if lowest_ratio_func is not None:
        print("The function with the lowest Related Ratio:")
        print(f"Function: {lowest_ratio_func.desc()}")
        print(f"    Related Ratio: {lowest_ratio:.2%}")
        print("-----------------------------------------------------------")
    return lowest_ratio


def process_sstore_recursive_analysis(ssa, remaining_instructions):

    results = []

    # 构建所有指令的字典
    all_instructions_by_variable = {}    
    for func in ssa.functions:
        # 遍历所有函数并保存指令
        for block in func:
            for insn in block:
                # 统一处理 return_value 和 arguments
                for related_var in [insn.return_value] + (insn.arguments if hasattr(insn, 'arguments') else []):
                    if related_var is not None and related_var not in all_instructions_by_variable:
                        all_instructions_by_variable[related_var] = insn
    # print(f"Total variables with instructions: {len(all_instructions_by_variable)}")

    updated_remaining_instructions = iterative_sstore_analysis(
        remaining_instructions, all_instructions_by_variable
    )
    # print(f"Remaining instructions after SSTORE analysis ({len(updated_remaining_instructions)}):")
    # for insn in updated_remaining_instructions:
    #     print(f"\t{insn}")

    results.append({
        "function": func.desc(),
        "remaining_instructions": updated_remaining_instructions,
    })

    return results

def iterative_sstore_analysis(remaining_instructions, all_instructions_by_variable):

    # print(f"Initial remaining instructions: {len(remaining_instructions)}")
    while True:

        sstore_instructions = [
            insn for insn in remaining_instructions
            if hasattr(insn, 'insn') and insn.insn.name == 'SSTORE'
        ]
        # print(f"Detected SSTORE instructions ({len(sstore_instructions)}):")
        if not sstore_instructions:

            break

        for insn in sstore_instructions:
            variable = insn.arguments[1]  # SSTORE 的目标变量(Value)
            # print(f"Analyzing SSTORE at {insn} for variable {variable}")


            trace = backward_analysis(variable, all_instructions_by_variable)

     
            remaining_instructions -= set(trace)

        remaining_instructions -= set(sstore_instructions)

    return remaining_instructions





def backward_analysis(variable, all_instructions_by_variable, visited=None):

    if visited is None:
        visited = set()

    trace = [] 
    variables_to_trace = [variable]  

    while variables_to_trace:
        current_variable = variables_to_trace.pop(0)

        if current_variable in visited:
            continue

        visited.add(current_variable)  

        if str(current_variable).startswith('#'):
            continue

        if current_variable in all_instructions_by_variable:
            insn = all_instructions_by_variable[current_variable]
            trace.append(insn) 

            for argument in insn.arguments:
                if argument not in visited: 
                    variables_to_trace.append(argument)
        else:
            trace.append(f"No definition found for variable {current_variable}")
    return trace