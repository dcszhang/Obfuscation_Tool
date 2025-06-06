# first_feature.py
import Obfuscation
# 定义地址变量来保存所有路径
all_trace_paths = {}
# 定义全局变量，用于存储所有变量的追踪路径
all_traces = {}  # 将列表改为字典
# 定义全局变量来保存每个地址变量的树
all_trees = {}

def save_trace_to_global(variable, trace):
    """保存回溯路径到全局变量"""
    global all_trace_paths
    all_trace_paths[variable] = trace


def analyze_contract_complex(ssa):
    """
    分析合约中是否可以发送 Ether，并追踪相关指令路径。
    
    :param ssa: 静态单赋值形式的分析对象
    :param backward_analysis: 回溯分析函数
    :param build_tree_structure: 构建树形结构的函数
    """
    # 存储所有指令
    all_instructions_by_variable = {}
    max_trace_info = {'max_sum': 0, 'transfer_number': 0, 'trace_step': 0, 'tree_height': 0, 'string_operations': 0, 'instruction': None}
    # 遍历所有函数并保存指令
    for function in ssa.functions:
        for block in function:
            for insn in block:
                if hasattr(insn, 'return_value') and insn.return_value is not None:
                    variable = insn.return_value  # 获取指令的返回值变量
                    all_instructions_by_variable[variable] = insn  # 将变量和对应的指令保存到字典中
    func_index = 0
    all_traces = {}  # 初始化追踪字典
    transfer_number = 0 # 初始化转账次数
    # print("[+] Contract can send ether from following functions:")
    for function in sorted(ssa.functions, key=lambda f: f.offset):
        # 初始化每个函数的追踪列表
        all_traces[func_index] = []
        for block in function:
            for insn in block:
                # print(f"\t\t{insn}")
                if isinstance(insn, str):
                    tokens = insn.split()
                    if any(op in tokens for op in ['CALL', 'DELEGATECALL']):
                        address_source = tokens[1]  # 假设第二个token是地址来源
                        # 回溯分析，记录沿途的指令路径
                        trace = backward_analysis(address_source, all_instructions_by_variable)
                        tree_root = build_tree_structure(address_source, all_instructions_by_variable)
                        # print(f'Trasfer Address Trace:')
                        # for t in trace:
                        #     print(f'\t{t}')
                        print(f'This is the {transfer_number} transfer')
                        print(f'    (1) Found Transfer Address instruction:\n\t    {writer_insn}')
                        print(f'    (2) trace_step: {len(trace)}')
                        analyze_saved_traces(trace,address_source, max_trace_info)  # 分析保存的路径
                        print("-----------------------------------------------------------")
                elif hasattr(insn.insn, 'name'):
                    if insn.insn.name == 'SELFDESTRUCT':
                        address = insn.arguments[0]
                    elif insn.insn.name in ('CALL', 'DELEGATECALL'):
                        address = insn.arguments[1]
                        writer_insn = address.writer
                        address_source = insn.arguments[1]
                        transfer_number += 1
                        trace = backward_analysis(address_source, all_instructions_by_variable)
                        # print(f'Trasfer Address Trace:')
                        # for t in trace:
                        #     print(f'\t{t}')
                        tree_root = build_tree_structure(address_source, all_instructions_by_variable)
                        print(f'This is the {transfer_number} transfer')
                        print(f'    (1) Found Transfer Address instruction:\n\t    {writer_insn}')
                        print(f'    (2) trace_step: {len(trace)}')
                        max_trace_info['current_transfer'] = transfer_number
                        analyze_saved_traces(trace,address_source, max_trace_info)  # 分析保存的路径
                        print("-----------------------------------------------------------")
    print("The transfer with the highest trace_step + Tree height + String Operation times:")
    print(f"This is the {max_trace_info['transfer_number']} transfer")
    print(f"    (1) Found Transfer Address instruction:\n\t    {max_trace_info['instruction']}")
    print(f"    (2) trace_step: {max_trace_info['trace_step']}")
    print(f"    (3) Tree height: {max_trace_info['tree_height']}")
    print(f"    (4) String Operation times: {max_trace_info['string_operations']}")
    print("-----------------------------------------------------------")
    # 返回所需的数据
    return (max_trace_info['trace_step'], max_trace_info['tree_height'], max_trace_info['string_operations'])

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
    # 保存路径到全局变量
    save_trace_to_global(variable, trace)
    return trace


def build_tree_structure(variable, all_instructions_by_variable, visited=None):

    if visited is None:
        visited = set()

    tree_root = TreeNode(variable)  # 创建树的根节点
    variables_to_trace = [(variable, tree_root)]  # 初始化要追踪的变量列表，包含树节点

    while variables_to_trace:
        current_variable, current_node = variables_to_trace.pop(0)

        # 如果已经访问过该变量，则跳过，防止死循环
        if current_variable in visited:
            continue

        visited.add(current_variable)  # 将当前变量标记为已访问

        # 如果当前变量是常量，直接跳过回溯
        if str(current_variable).startswith('#'):
            continue

        # 查找该变量的定义
        if current_variable in all_instructions_by_variable:
            insn = all_instructions_by_variable[current_variable]

            # 对该指令的操作数进行回溯，并构建子节点
            for argument in insn.arguments:
                if argument not in visited:
                    child_node = TreeNode(argument)  # 为操作数创建子节点
                    current_node.add_child(child_node)  # 将子节点加入当前节点
                    variables_to_trace.append((argument, child_node))  # 将子节点加入追踪队列

    # 保存树到全局变量
    save_tree_to_global(variable, tree_root)
    return tree_root  # 返回树的根节点


def analyze_saved_traces(trace,variable,max_trace_info):

    # 遍历 all_trace_paths 中的所有保存路径
    # for variable, trace in all_trace_paths.items():
    String_Operation_times=0
    for insn in trace:
        if isinstance(insn, str):
            tokens = insn.split()
            if any(op in tokens for op in ['MLOAD', 'CALLDATALOAD']):
                String_Operation_times += 1
            elif 'ADD' in tokens:
                String_Operation_times += 1
            elif any(op in tokens for op in ['CALL', 'DELEGATECALL']):
                String_Operation_times += 1
        # 如果是具有属性的对象，按原逻辑处理
        elif hasattr(insn, 'insn') and hasattr(insn.insn, 'name'):
            if insn.insn.name in ['MLOAD', 'CALLDATALOAD']:
                String_Operation_times += 1
            elif insn.insn.name == 'ADD':
                String_Operation_times += 1
            elif insn.insn.name in ['CALL', 'DELEGATECALL']:
                String_Operation_times += 1
    # 计算树的层数
    tree_root = all_trees.get(variable)
    if tree_root:
        tree_height = tree_root.get_height()
    else:
        tree_height = 0  # 如果没有树，就设置高度为0
    # 输出树的高度和字符串操作次数
    print(f"    (3) Tree height: {tree_height}")
    print(f"    (4) String Operation times: {String_Operation_times}")


     # 计算指标总和
    trace_sum = len(trace) + tree_height + String_Operation_times

    # 更新最大值
    if trace_sum > max_trace_info['max_sum']:
        max_trace_info.update({
            'max_sum': trace_sum,
            'transfer_number': max_trace_info['current_transfer'],
            'trace_step': len(trace),
            'tree_height': tree_height,
            'string_operations': String_Operation_times,
            'instruction': trace[0] if trace else None
        })
            


def save_tree_to_global(variable, tree):

    global all_trees
    all_trees[variable] = tree

class TreeNode:
    def __init__(self, variable):
        self.variable = variable  # 当前节点对应的变量
        self.children = []  # 子节点列表

    def add_child(self, child_node):
        """将子节点添加到当前节点"""
        self.children.append(child_node)

    def __repr__(self):
        """便于调试，打印树节点的变量名"""
        return f"TreeNode({self.variable})"
    
    def print_tree(self, level=0, prefix=""):
            """递归打印整个树结构，使用更加直观的树形格式"""
            # 打印当前节点
            print(f"{prefix}{self.variable}")
            # 遍历子节点，调整前缀以显示树的结构
            for i, child in enumerate(self.children):
                # 如果是最后一个子节点，使用 "└──"，否则使用 "├──"
                if i == len(self.children) - 1:
                    child_prefix = prefix + "    "  # 对齐格式
                    child.print_tree(level + 1, prefix + "└── ")
                else:
                    child_prefix = prefix + "│   "  # 对齐格式
                    child.print_tree(level + 1, prefix + "├── ")
    def get_height(self):
            """递归计算树的高度"""
            if not self.children:
                return 1  # 如果没有子节点，树的高度为1
            return 1 + max(child.get_height() for child in self.children)