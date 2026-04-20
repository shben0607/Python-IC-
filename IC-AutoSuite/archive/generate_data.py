import pandas as pd
import numpy as np

def generate_and_clean_data():
    # 將量級提升到 100,000 筆 (模擬大規模量產測試)
    num_samples = 100000 
    data = {
        'Chip_ID': range(1, num_samples + 1),
        'Voltage': np.random.normal(1.8, 0.08, num_samples) # 增加一點標準差讓 FAIL 變多
    }
    df = pd.DataFrame(data)
    
    # 增加髒數據的比例 (模擬機台噪訊)
    noise_indices = np.random.choice(df.index, size=500, replace=False)
    df.loc[noise_indices, 'Voltage'] = -99.0
    
    # 執行清潔 (在 10 萬筆數據中過濾，這才有自動化的價值)
    df_cleaned = df[df['Voltage'] > 0].dropna().copy()
    
    df_cleaned.to_csv("heavy_test_data.csv", index=False)
    return len(df) - len(df_cleaned)

if __name__ == "__main__":
    create_mock_data()