from datetime import date, datetime

def gen_header(module_name, filter_des):
    header = f"""
////////////////////////////////////////////////////////////////////////////////////////
// File Name: {module_name}.sv
// Author: filter_designer.py
// Date: {date.today()} - {datetime.now().strftime("%H:%M:%S")}
// Description: {filter_des}
////////////////////////////////////////////////////////////////////////////////////////
"""
    return header


def iir_gen(filter_des, module_name, b_coeffs, a_coeffs, width=16):
    M = len(b_coeffs) - 1
    N = len(a_coeffs) - 1

    # ================= REGISTERS =================
    x_regs = "\n".join(
        [f"logic signed [{width-1}:0] x{i};" for i in range(M + 1)]
    )
    y_regs = "\n".join(
        [f"logic signed [{width-1}:0] y{i};" for i in range(1, N + 1)]
    )

    # ================= EXPRESSIONS =================
    ff_terms = " + ".join([f"x{i} * {b_coeffs[i]}" for i in range(M + 1)])
    fb_terms = " + ".join([f"y{i} * {a_coeffs[i]}" for i in range(1, N + 1)])

    y_expr = f"{ff_terms} - ({fb_terms})" if fb_terms else ff_terms

    # ================= RESET =================
    reset_lines = "\n".join(
        [f"        x{i} <= '0;" for i in range(M + 1)]
    )
    if N > 0:
        reset_lines += "\n" + "\n".join(
            [f"        y{i} <= '0;" for i in range(1, N + 1)]
        )

    # ================= SHIFTS =================
    x_shift_lines = "\n".join(
        [f"        x{i} <= x{i-1};" for i in range(M, 0, -1)]
    )

    y_shift_lines = "\n".join(
        [f"        y{i} <= y{i-1};" for i in range(N, 1, -1)]
    )

    # ================= RTL =================
    rtl = f"""{gen_header(module_name, filter_des)}
module {module_name} (
    input  logic clk,
    input  logic rst_n,
    input  logic signed [{width-1}:0] x_in,
    output logic signed [{width-1}:0] y_out
);

{x_regs}
{y_regs}

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
{reset_lines}
    end else begin
        // Shift registers
{x_shift_lines}
{y_shift_lines}
        x0 <= x_in;
    end
end

// Compute output (Direct Form I)
assign y_out = {y_expr};

endmodule
"""
    return rtl
