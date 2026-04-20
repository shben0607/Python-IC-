import os
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

import numpy as np
import pandas as pd

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Span, WheelZoomTool
from bokeh.plotting import figure, output_file, save
from bokeh.resources import CDN


# -----------------------------
# VCD parser
# -----------------------------
def parse_vcd_file(file_path):
    """
    Read a simple VCD file and extract SDA / SCL waveform data.
    Also detect I2C start condition:
    SDA: 1 -> 0 while SCL stays at 1
    """
    sda_data = []
    scl_data = []
    start_bits = []

    sda_state = 1
    scl_state = 1
    prev_sda = 1
    curr_time = 0

    # initial state
    sda_data.append({"t": 0, "v": 1})
    scl_data.append({"t": 0, "v": 1})

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            # skip empty lines or VCD control lines
            if not line or line.startswith("$"):
                continue

            # time marker
            if line.startswith("#"):
                try:
                    curr_time = int(line[1:])
                except ValueError:
                    continue
                continue

            # normal signal line, format like 1a / 0b
            try:
                value = int(line[0])
                signal = line[1:]

                if signal == "a":   # SDA
                    prev_sda = sda_state
                    sda_state = value
                    sda_data.append({"t": curr_time, "v": sda_state})

                    # detect I2C start bit
                    if scl_state == 1 and prev_sda == 1 and sda_state == 0:
                        start_bits.append(curr_time)

                elif signal == "b":   # SCL
                    scl_state = value
                    scl_data.append({"t": curr_time, "v": scl_state})

            except (ValueError, IndexError):
                # skip bad line instead of crashing
                continue

    return pd.DataFrame(sda_data), pd.DataFrame(scl_data), start_bits


# -----------------------------
# Main GUI App
# -----------------------------
class IntegratedICApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IC 檢測程式")
        self.root.geometry("480x460")

        self.data_file = "industrial_data.csv"
        self.vcd_file = "test_logic.vcd"

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self.root,
            text="IC 檢測與分析工具",
            font=("微軟正黑體", 18, "bold"),
            fg="#2c3e50"
        ).pack(pady=20)

        btn_style = {
            "width": 35,
            "pady": 8,
            "font": ("微軟正黑體", 10)
        }

        tk.Button(
            self.root,
            text="1. 產生測試資料",
            command=self.generate_test_files,
            **btn_style
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="2. 分析資料並顯示圖表",
            command=self.analyze_voltage_data,
            bg="#8e44ad",
            fg="white",
            **btn_style
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="3. 顯示 VCD 波形",
            command=self.show_vcd_waveform,
            bg="#3498db",
            fg="white",
            **btn_style
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="4. 開啟目前資料檔案",
            command=self.open_data_file,
            bg="#27ae60",
            fg="white",
            **btn_style
        ).pack(pady=5)

        self.status_label = tk.Label(
            self.root,
            text="系統狀態：就緒",
            fg="gray",
            font=("微軟正黑體", 10)
        )
        self.status_label.pack(side="bottom", pady=10)

    def set_status(self, text):
        self.status_label.config(text=f"系統狀態：{text}")
        self.root.update_idletasks()

    # -----------------------------
    # Function 1: generate data
    # -----------------------------
    def generate_test_files(self):
        self.set_status("正在產生測試資料...")

        try:
            num = 10000

            # create voltage data around 1.8V
            voltage = np.random.normal(1.8, 0.05, num)

            # manually inject abnormal segment
            voltage[4000:4500] += 0.2

            df = pd.DataFrame({
                "ID": np.arange(1, num + 1),
                "V": voltage
            })
            df.to_csv(self.data_file, index=False, encoding="utf-8-sig")

            # create simple VCD sample
            with open(self.vcd_file, "w", encoding="utf-8") as f:
                f.write(
                    "$timescale 1ns $end\n"
                    "$enddefinitions $end\n"
                    "#0\n1a\n1b\n"
                    "#20\n0a\n1b\n"
                    "#40\n0a\n0b\n"
                    "#80\n1a\n1b\n"
                )

            self.set_status("測試資料產生完成")
            messagebox.showinfo(
                "成功",
                f"已產生：\n{self.data_file}\n{self.vcd_file}"
            )

        except Exception as e:
            self.set_status("產生資料失敗")
            messagebox.showerror("錯誤", f"產生測試資料失敗：\n{e}")

    # -----------------------------
    # Function 2: analyze csv
    # -----------------------------
    def analyze_voltage_data(self):
        if not os.path.exists(self.data_file):
            messagebox.showwarning("提醒", f"找不到檔案：{self.data_file}")
            return

        self.set_status("正在分析電壓資料...")

        try:
            df = pd.read_csv(self.data_file)

            if "ID" not in df.columns or "V" not in df.columns:
                messagebox.showerror("錯誤", "CSV 格式不正確，必須包含 ID 和 V 欄位。")
                self.set_status("資料分析失敗")
                return

            # down sample for faster plotting
            df_sample = df.iloc[::200, :].copy()
            source = ColumnDataSource(df_sample)

            mean_v = df["V"].mean()
            std_v = df["V"].std()
            upper_limit = mean_v + 3 * std_v
            lower_limit = mean_v - 3 * std_v

            # trend plot
            p1 = figure(
                title="Voltage Trend",
                width=950,
                height=350,
                tools="pan,wheel_zoom,reset,hover",
                x_axis_label="Sample ID",
                y_axis_label="Voltage (V)"
            )

            p1.line("ID", "V", source=source, color="#34495e", alpha=0.6, line_width=2)
            p1.circle("ID", "V", source=source, size=3, color="#9b59b6", alpha=0.35)

            p1.add_layout(
                Span(
                    location=upper_limit,
                    dimension="width",
                    line_color="red",
                    line_dash="dashed",
                    line_width=2
                )
            )
            p1.add_layout(
                Span(
                    location=lower_limit,
                    dimension="width",
                    line_color="orange",
                    line_dash="dashed",
                    line_width=2
                )
            )

            hover = p1.select_one(HoverTool)
            if hover:
                hover.tooltips = [
                    ("ID", "@ID"),
                    ("Voltage", "@V{0.000}")
                ]

            p1.toolbar.active_scroll = p1.select_one(WheelZoomTool)

            # histogram
            hist, edges = np.histogram(df["V"], bins=50)

            p2 = figure(
                title="Voltage Distribution",
                width=950,
                height=260,
                x_axis_label="Voltage (V)",
                y_axis_label="Count"
            )

            p2.quad(
                top=hist,
                bottom=0,
                left=edges[:-1],
                right=edges[1:],
                fill_color="#3498db",
                line_color="white",
                alpha=0.8
            )

            save_path = os.path.join(os.getcwd(), "big_data_analysis.html")
            output_file(filename=save_path, title="Big Data Diagnosis")
            save(column(p1, p2), resources=CDN)

            webbrowser.open(f"file://{save_path}")
            self.set_status("資料分析完成")

        except Exception as e:
            self.set_status("資料分析失敗")
            messagebox.showerror("錯誤", f"分析資料時發生問題：\n{e}")

    # -----------------------------
    # Function 3: show VCD waveform
    # -----------------------------
    def show_vcd_waveform(self):
        file_path = filedialog.askopenfilename(
            title="選擇 VCD 檔案",
            filetypes=[("VCD files", "*.vcd")]
        )

        if not file_path:
            file_path = self.vcd_file

        if not os.path.exists(file_path):
            messagebox.showwarning("提醒", f"找不到檔案：{file_path}")
            return

        self.set_status("正在解析 VCD 波形...")

        try:
            df_sda, df_scl, start_bits = parse_vcd_file(file_path)

            p_sda = figure(
                title="SDA Waveform",
                width=950,
                height=250,
                tools="pan,wheel_zoom,reset,hover",
                x_axis_label="Time (ns)",
                y_axis_label="SDA"
            )
            p_sda.step(
                x="t",
                y="v",
                source=ColumnDataSource(df_sda),
                mode="after",
                color="red",
                line_width=3
            )

            p_scl = figure(
                title="SCL Waveform",
                width=950,
                height=250,
                x_range=p_sda.x_range,
                tools="pan,wheel_zoom,reset,hover",
                x_axis_label="Time (ns)",
                y_axis_label="SCL"
            )
            p_scl.step(
                x="t",
                y="v",
                source=ColumnDataSource(df_scl),
                mode="after",
                color="blue",
                line_width=3
            )

            p_scl.toolbar.active_scroll = p_scl.select_one(WheelZoomTool)

            save_path = os.path.join(os.getcwd(), "timing_analysis.html")
            output_file(filename=save_path, title="Timing Verification")
            save(column(p_sda, p_scl), resources=CDN)

            webbrowser.open(f"file://{save_path}")
            self.set_status("VCD 分析完成")

            if start_bits:
                messagebox.showinfo(
                    "時序偵測結果",
                    f"偵測到 Start Bit 時間點：\n{start_bits} ns"
                )
            else:
                messagebox.showinfo("時序偵測結果", "未偵測到 Start Bit。")

        except Exception as e:
            self.set_status("VCD 分析失敗")
            messagebox.showerror("錯誤", f"解析 VCD 檔案失敗：\n{e}")

    # -----------------------------
    # Extra helper
    # -----------------------------
    def open_data_file(self):
        if not os.path.exists(self.data_file):
            messagebox.showwarning("提醒", f"找不到檔案：{self.data_file}")
            return

        try:
            abs_path = os.path.abspath(self.data_file)
            webbrowser.open(f"file://{abs_path}")
            self.set_status("已開啟資料檔案")
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟檔案失敗：\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedICApp(root)
    root.mainloop()