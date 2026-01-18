import tkinter as tk
from tkinter import ttk
import filter_designer
import rtl_gen
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import sosfreqz


class FilterGUI:
    def __init__(self, root):
        self.root = root
        root.title("Digital Filter Designer GUI")
        root.geometry("1200x850")
        root.configure(bg="#e8eef7")

        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="y", padx=(0, 10), pady=10)

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", padding=5)

        title_lbl = ttk.Label(control_frame, text="Filter Parameters", font=("Segoe UI", 14, "bold"))
        title_lbl.pack(pady=(0, 15))

        def add_field(label):
            lbl = ttk.Label(control_frame, text=label)
            lbl.pack(anchor="w")
            entry = ttk.Entry(control_frame)
            entry.pack(fill="x", pady=(0, 10))
            return entry

        # ================= FILTER FIELDS =================
        self.order_entry = add_field("Filter Order")

        ttk.Label(control_frame, text="Filter Type").pack(anchor="w")
        self.type_box = ttk.Combobox(control_frame, values=["butter", "cheby1", "cheby2", "ellip"])
        self.type_box.pack(fill="x", pady=(0, 10))

        ttk.Label(control_frame, text="Response Type").pack(anchor="w")
        self.response_box = ttk.Combobox(control_frame, values=["lowpass", "highpass", "bandpass", "bandstop"])
        self.response_box.pack(fill="x", pady=(0, 10))

        self.wn_entry = add_field("Wn (space separated if 2 values)")
        self.fs = add_field("Sampling frequency (fs)")
        self.ripple_entry = add_field("Ripple (optional)")
        self.min_att_entry = add_field("Min Attenuation (optional)")

        ttk.Button(control_frame, text="Calculate filter", command=self.run_filter).pack(pady=10, fill="x")
        ttk.Button(control_frame, text="Save coefficients to csv", command=self.save_csv).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="Save plot to png", command=self.save_plot_image).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="Toggle X-axis (Wn / Hz)", command=self.toggle_x_axis).pack(pady=5, fill="x")

        # ================= RTL SECTION =================
        rtl_title = ttk.Label(control_frame, text="RTL Generation", font=("Segoe UI", 12, "bold"))
        rtl_title.pack(pady=(20, 10))

        self.module_entry = add_field("RTL Module Name")
        self.width_entry = add_field("Coefficient Bit Width")
        self.frac_prec_entry = add_field("Fractional Precision (bits)")

        ttk.Button(control_frame, text="Generate RTL", command=self.generate_rtl).pack(pady=5, fill="x")

        self.status_label = ttk.Label(control_frame, text="", foreground="green")
        self.status_label.pack(pady=(5, 0), fill="x")

        separator = ttk.Separator(main_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=10, pady=10)

        plot_container = ttk.Frame(main_frame)
        plot_container.pack(side="left", fill="both", expand=True, padx=(25, 0), pady=5)

        self.plot_frame = ttk.Frame(plot_container)
        self.plot_frame.pack(fill="both", expand=True)

        self.canvas = None

        # ================= STATE =================
        self.latest_w = None
        self.latest_h = None
        self.latest_sos = None
        self.latest_filename = None
        self.x_axis_mode = "wn"

    # ================= FILTER LOGIC =================
    def run_filter(self):
        try:
            order = int(self.order_entry.get())
            ftype = self.type_box.get()
            response = self.response_box.get()

            wn_vals = [float(v) for v in self.wn_entry.get().split()]
            wn = wn_vals[0] if len(wn_vals) == 1 else wn_vals

            fs = float(self.fs.get()) if self.fs.get() else 1.0
            ripple = float(self.ripple_entry.get()) if self.ripple_entry.get() else None
            min_att = float(self.min_att_entry.get()) if self.min_att_entry.get() else None

            def convert_wn(v):
                return (v * (fs / 2)) if v <= 1 else v

            wn = [convert_wn(v) for v in wn] if isinstance(wn, list) else convert_wn(wn)

            # === FIXED: filename now stored ===
            w, h, filename = filter_designer.run_filter_from_gui(
                order, ftype, wn, response, ripple, min_att, fs
            )

            self.latest_w = w
            self.latest_h = h
            self.latest_filename = filename

            self.latest_sos = filter_designer.calc_filter_coeffs(
                order, ftype, wn, response, ripple, min_att, fs
            )[2]

            self.plot_response(w, h, ftype, response, order)

            self.status_label.config(text="Filter calculated successfully.", foreground="blue")

        except Exception as e:
            self.status_label.config(text=f"Error: {e}", foreground="red")

    # ================= SAVE FUNCTIONS =================
    def save_csv(self):
        if self.latest_filename is None:
            self.status_label.config(text="No filter calculated yet!", foreground="red")
            return
        with open(self.latest_filename, "w") as f:
            for wi, hi in zip(self.latest_w, self.latest_h):
                f.write(f"{wi},{hi}\n")
        self.status_label.config(text=f"Saved {self.latest_filename}", foreground="green")

    def save_plot_image(self):
        if self.canvas is None:
            return
        self.canvas.figure.savefig(self.latest_filename.replace(".csv", ".png"))

    # ================= RTL GENERATION =================
    def rename_filter(self, f):
        return {
            "butter": "Butterworth",
            "cheby1": "Chebyshev I",
            "cheby2": "Chebyshev II",
            "ellip": "Elliptic",
        }[f]

    def gen_filter_des(self):
        txt = "This code describes a SystemVerilog IIR filter:"
        txt += f"\n// Order: {self.order_entry.get()}"
        txt += f"\n// Type: {self.rename_filter(self.type_box.get())}"
        txt += f"\n// Response: {self.response_box.get()}"
        return txt

    def generate_rtl(self):
        if self.latest_sos is None:
            self.status_label.config(text="No filter available!", foreground="red")
            return

        module = self.module_entry.get().strip()
        width = int(self.width_entry.get())
        frac_prec = int(self.frac_prec_entry.get())

        # ⚠️ NOTE: still only first SOS (your original behavior)
        b = self.latest_sos[0][:3]
        a = self.latest_sos[0][3:]

        rtl = rtl_gen.iir_gen(self.gen_filter_des(), module, b, a, width, frac_prec)

        with open(f"{module}.sv", "w") as f:
            f.write(rtl)

        self.status_label.config(text=f"RTL generated: {module}.sv", foreground="green")

    # ================= PLOT =================
    def toggle_x_axis(self):
        self.x_axis_mode = "hz" if self.x_axis_mode == "wn" else "wn"
        self.plot_response(self.latest_w, self.latest_h,
                           self.type_box.get(),
                           self.response_box.get(),
                           int(self.order_entry.get()))

    def plot_response(self, w, h, ftype, response, order):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)

        h_db = 20 * np.log10(np.abs(h))
        fs = float(self.fs.get()) if self.fs.get() else 1.0

        x = w / (fs / 2) if self.x_axis_mode == "wn" else w
        ax.plot(x, h_db)
        ax.grid(True)
        ax.set_ylabel("Gain (dB)")
        ax.set_xlabel("Normalized Frequency" if self.x_axis_mode == "wn" else "Frequency (Hz)")
        ax.set_title(f"{order}th Order {self.rename_filter(ftype)} {response}")

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    FilterGUI(root)
    root.mainloop()
