import dask.dataframe as dd
from dask.distributed import Client
from dask.diagnostics import ProgressBar
import subprocess
import time
import pandas as pd  # 用于 pd.isna 检查
def process_task(row):
    """
    以一整行 row（含 bytecode, address）为输入，
    返回一个 dict：{'index':..., 'address':..., 'output':...}。
    Dask 会将这个 dict “展开”成多列。
    """
    idx = row.name
    bytecode = row["bytecode"]
    address = row["address"]
    # ======= 新增：检查缺失值 =======
    if pd.isna(bytecode) or bytecode is None:
        print(f"⚠️ 进程 {idx} 的 bytecode 为空，跳过！")
        return {
            "index": int(idx + 1),
            "address": address,
            "output": "Error: Missing bytecode"
        }
    # 去掉 0x 前缀
    if bytecode.startswith("0x"):
        bytecode = bytecode[2:]

    try:
        # print(f"⏳ 进程 {idx} 开始执行 rattle-cli.py")
        result = subprocess.run(
            ["python", "rattle-cli.py"],
            input=bytecode,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=400  # 超过 60 秒跳过
        )
        # 只取最后一行输出
        last_line = result.stdout.strip().split("\n")[-1] if result.stdout else "No output"
        print(f"✅ 进程 {idx} 完成: {last_line[:50]}...")
        return {
            "index": int(idx + 1),
            "address": address,
            "output": last_line
        }

    except subprocess.TimeoutExpired:
        print(f"⚠️ 进程 {idx} 超时（>400s），跳过！")
        return {
            "index": int(idx + 1),
            "address": address,
            "output": "Error: Timeout exceeded"
        }

    except Exception as e:
        return {
            "index": int(idx + 1),
            "address": address,
            "output": f"Error: {e}"
        }


if __name__ == "__main__":
    # 1) 启动 Dask，使用 25 个进程 (而非线程)
    client = Client(
        n_workers=10,
        threads_per_worker=1,
        processes=True,
        local_directory="dask_tmp",
    )
    # print(client)  # 打印 Dask Worker 信息
    print("Dashboard:", client.dashboard_link)
    # 2) CSV 文件路径
    csv_path = "test.csv"
    output_csv_path = "output.csv"

    # 1) 用 ~200MB blocksize 自动分块
    df = dd.read_csv(csv_path, blocksize="50MB")
    print(f"初始分区数: {df.npartitions}")

    # 2) 如果想固定到 25 分区，再 repartition
    df = df.repartition(npartitions=10)
    print(f"最终分区数: {df.npartitions}")

    # 4) 用 df.apply(...)，返回 dict，并指定 result_type="expand"
    #    这样 Dask 会把字典“展开”成多列 (index, address, output)
    #    meta 用于告诉 Dask 每列数据类型
    result_ddf = df.apply(
        process_task,
        axis=1,
        result_type="expand",   # 关键点：展开 dict 到多列
        meta={
            "index": "int64",
            "address": "object",
            "output": "object"
        }
    )

    # 5) 用 Dask 自带的进度条
    with ProgressBar():
        final_df = result_ddf.compute()

    # final_df 是一个 Pandas DataFrame，有 3 列 (index, address, output)
    # 6) 写出到 CSV
    final_df.to_csv(output_csv_path, index=False)

    print(f"✅ 任务完成！已保存到 {output_csv_path}")
