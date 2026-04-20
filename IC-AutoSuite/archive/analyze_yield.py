import pandas as pd
import matplotlib.pyplot as plt

def run_analysis():
    # 1. 讀取第一步產生的資料
    try:
        df = pd.read_csv("test_data.csv")
    except FileNotFoundError:
        print("錯誤：找不到 test_data.csv，請先執行第一步的程式！")
        return

    # 2. 設定判定標準 (假設 Google/MTK 規範是 1.72V 到 1.88V 之間)
    lower_limit = 1.72
    upper_limit = 1.88

    # 3. 自動判定 Pass/Fail
    # 使用 pandas 的邏輯判斷，這比用 for 迴圈快幾百倍
    df['Status'] = df['Voltage'].apply(
        lambda x: 'PASS' if lower_limit <= x <= upper_limit else 'FAIL'
    )

    # 4. 計算成效數據
    total_count = len(df)
    pass_count = len(df[df['Status'] == 'PASS'])
    fail_count = total_count - pass_count
    yield_rate = (pass_count / total_count) * 100

    print("-" * 30)
    print(f"分析完成！")
    print(f"總測試數量: {total_count}")
    print(f"合格數量 (PASS): {pass_count}")
    print(f"不合格數量 (FAIL): {fail_count}")
    print(f"良率 (Yield Rate): {yield_rate:.2f}%")
    print("-" * 30)

    # 5. 繪製專業統計圖表
    plt.figure(figsize=(10, 6))
    
    # 畫出電壓分佈直方圖
    plt.hist(df['Voltage'], bins=30, color='skyblue', edgecolor='black', alpha=0.7, label='Voltage Distribution')
    
    # 畫出規格界限紅線 (LSL/USL)
    plt.axvline(lower_limit, color='red', linestyle='--', linewidth=2, label=f'Lower Limit ({lower_limit}V)')
    plt.axvline(upper_limit, color='red', linestyle='--', linewidth=2, label=f'Upper Limit ({upper_limit}V)')
    
    # 設定圖表標題與標籤
    plt.title(f"IC Wafer Test Yield Analysis\nFinal Yield: {yield_rate:.2f}%", fontsize=14)
    plt.xlabel("Voltage (V)")
    plt.ylabel("Chip Count")
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 6. 自動儲存圖表 (面試時可以展示這張圖片)
    plt.savefig("yield_report.png")
    print("報告圖片已儲存為 yield_report.png")
    plt.show()

if __name__ == "__main__":
    run_analysis()