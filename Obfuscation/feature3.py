# Third_feature.py
def analyze_contract_external(ssa):

    all_instructions_by_variable = {}

    all_trace_paths = {}

    for function in ssa.functions:
        for block in function:
            for insn in block:
                if hasattr(insn, 'return_value') and insn.return_value is not None:
                    variable = insn.return_value  
                    all_instructions_by_variable[variable] = insn  

    for function in sorted(ssa.functions, key=lambda f: f.offset):

        for block in function:
            for insn in block:
                # print(f"\t\t{insn}")
                if insn.insn.name == 'SELFDESTRUCT':
                    address = insn.arguments[0]
                    # print(f'\t\t\t{address.writer}')
                elif insn.insn.name in ('CALL', 'DELEGATECALL'):
                    address = insn.arguments[1]
                    value = insn.arguments[2]

                    trace_address= backward_analysis(address, all_instructions_by_variable)
                    trace_value = backward_analysis(value, all_instructions_by_variable)


                    all_trace_paths[address] = trace_address
                    all_trace_paths[value] = trace_value

        results = analyze_saved_traces(all_trace_paths)
        true_or_false = False
        for result in results:
            # print(f"Variable {result['variable']} has external call: {result['has_external_call']}")
            if result['has_external_call']:
                true_or_false = True

    print(f"(6)Address and Value in Transfer(External Call):{true_or_false}")
    print("-----------------------------------------------------------")
    return true_or_false
            

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
            # print(f"Constant value encountered: {current_variable}")
            continue


        if current_variable in all_instructions_by_variable:
            insn = all_instructions_by_variable[current_variable]
            trace.append(insn)  # 记录当前指令
            # print(f"Found definition of {current_variable}: {insn}")


            for argument in insn.arguments:
                if argument not in visited: 
                    variables_to_trace.append(argument)
        else:
            trace.append(f"No definition found for variable {current_variable}")
    return trace


def analyze_saved_traces(all_trace_paths):

    results = []
    for variable, trace in all_trace_paths.items():
        # print(f"Analyzing trace for variable: {variable}")
        has_external_call = False
        for insn in trace:
            if isinstance(insn, str):
               tokens = insn.split()
               if any(op in tokens for op in ['CALL', 'DELEGATECALL']):
                   has_external_call = True
            elif insn.insn.name in ['CALL', 'DELEGATECALL']:
                # print(f"Found external call at {insn}")
                has_external_call = True
        results.append({
            "variable": variable,
            "has_external_call": has_external_call
        })
    return results
