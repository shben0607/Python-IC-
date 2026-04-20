import re

def generate_testbench(v_file):
    with open(v_file, 'r') as f:
        content = f.read()

    # 1. 抓取模組名稱
    module_name = re.search(r'module\s+(\w+)', content).group(1)

    # 2. 抓取 input 和 output (包含位元寬度)
    inputs = re.findall(r'input\s+([\w\s\[\]:]+),', content)
    outputs = re.findall(r'output\s+([\w\s\[\]:]+)', content)

    print(f"解析成功！找到模組: {module_name}")
    print(f"輸入腳位: {inputs}")
    print(f"輸出腳位: {outputs}")

    # 3. 自動生成 Testbench 模板內容
    tb_content = f"""
`timescale 1ns / 1ps

module {module_name}_tb;
    // 信號宣告
"""
    for inp in inputs:
        tb_content += f"    reg {inp};\n"
    for outp in outputs:
        tb_content += f"    wire {outp};\n"

    tb_content += f"""
    // 實例化被測模組 (UUT)
    {module_name} uut (
"""
    # 這裡簡單寫，實際可更精細
    tb_content += "        // 請在此手動連線腳位\n    );\n\n"
    tb_content += "    initial begin\n        $dumpfile(\"dump.vcd\");\n        $dumpvars(0, {module_name}_tb);\n"
    tb_content += "        // 初始化信號\n        #100 $finish;\n    end\nendmodule"

    # 4. 儲存成新的檔案
    with open(f"{module_name}_tb.v", 'w') as f:
        f.write(tb_content)
    
    print(f"成功！已產出測試平台模板: {module_name}_tb.v")

if __name__ == "__main__":
    generate_testbench("counter.v")