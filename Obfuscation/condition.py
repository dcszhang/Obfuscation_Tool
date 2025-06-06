
import Obfuscation

def analyze_transfer_conditions(ssa):

    # 存储所有指令
    all_instructions_by_variable = {}
    for function in ssa.functions:
        for block in function:
            for insn in block:
                if hasattr(insn, 'return_value') and insn.return_value is not None:
                    variable = insn.return_value  # 获取指令的返回值变量
                    all_instructions_by_variable[variable] = insn  # 将变量和对应的指令保存到字典中

    # 创建 SystemDependenceGraph 实例
    sdg = Obfuscation.SystemDependenceGraph(ssa.functions)

    # 使用 CallBacktracking 对 SDG 中的函数进行回溯
    call_backtracking = Obfuscation.CallBacktracking(sdg)

    # 存储分析结果
    results = []
    true_or_false = False
    # 分析 CALL backward slicing 结果中的条件（PHI）
    for func, paths in call_backtracking.get_backtrack_results().items():
        for path in paths:
            for block in path:
                for insn in block:
                    if insn.insn.name in ("PHI","CMP", "EQ"):# , 
                        print(f"Found PHI node: {insn}")
                        for param in insn.arguments:
                            trace = backward_analysis(param, all_instructions_by_variable)
                            print(f'Trasfer Address Trace:')
                            # for t in trace:
                            #     print(f'\t{t}')
                            for traced_insn in trace:
                                if isinstance(traced_insn, str):
                                    tokens = traced_insn.split()
                                    if any(op in tokens for op in ['CALL']):
                                        true_or_false = True
                                        results.append({
                                            "function": func.desc(),
                                            "block": block.offset,
                                            "phi_param": param,
                                            "trace": trace
                                        })
                                elif traced_insn.insn.name in ("CALL"):
                                    true_or_false = True
                                    results.append({
                                        "function": func.desc(),
                                        "block": block.offset,
                                        "phi_param": param,
                                        "trace": trace
                                    })
    print(f"(9)Transfer have an external call condition to execute: {true_or_false}")
    print("--------------------------------------------------------------------------------------")
    print("                                      END                                             ")
    print("--------------------------------------------------------------------------------------")
    return true_or_false

def backward_analysis(variable, all_instructions_by_variable, visited=None):

    if visited is None:
        visited = set()

    trace = []  # 用于存储回溯路径中的所有指令
    variables_to_trace = [variable]  # 初始化要追踪的变量列表

    while variables_to_trace:
        current_variable = variables_to_trace.pop(0)

        # 如果已经访问过该变量，则跳过，防止死循环
        if current_variable in visited:
            continue

        visited.add(current_variable)  # 将当前变量标记为已访问
                # 如果当前变量是常量，直接跳过回溯
        if str(current_variable).startswith('#'):
            # print(f"Constant value encountered: {current_variable}")
            continue
        # 查找该变量的定义
        if current_variable in all_instructions_by_variable:
            insn = all_instructions_by_variable[current_variable]
            trace.append(insn)  # 记录当前指令
            # print(f"Found definition of {current_variable}: {insn}")

            # 对该指令的操作数进行回溯
            for argument in insn.arguments:
                if argument not in visited:  # 防止重复追踪
                    variables_to_trace.append(argument)
        else:
            trace.append(f"No definition found for variable {current_variable}")
    return trace
