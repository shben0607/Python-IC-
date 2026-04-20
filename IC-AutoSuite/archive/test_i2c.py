import matplotlib.pyplot as plt

def test_i2c_visual():
    # 模擬 10 個時間點的訊號
    time = list(range(10))
    scl = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    sda = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0] # 在時間點 4 發生跳變 (Start Bit)

    # 偵測邏輯
    start_point = -1
    for i in range(1, len(sda)):
        if scl[i] == 1 and sda[i-1] == 1 and sda[i] == 0:
            start_point = i
            break

    # 繪圖
    plt.figure(figsize=(10, 5))
    plt.step(time, scl, label="SCL (Clock)", where='post', color='blue', linewidth=2)
    plt.step(time, sda, label="SDA (Data)", where='post', color='red', linewidth=2)
    
    if start_point != -1:
        plt.annotate('START BIT DETECTED!', xy=(start_point, 0.5), xytext=(start_point+1, 0.8),
                     arrowprops=dict(facecolor='black', shrink=0.05), color='green', fontsize=12)
    
    plt.ylim(-0.5, 1.5)
    plt.title("I2C Protocol Logic Detection")
    plt.legend()
    plt.grid(True)
    print(f"偵測完成，跳變發生在時間點：{start_point}")
    plt.show() # 這行沒寫就絕對看不到圖！

test_i2c_visual()