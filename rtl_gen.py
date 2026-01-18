from datetime import date, datetime
from real2fix_point import real2fix_point

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


def iir_gen(filter_des, module_name, b_coeffs, a_coeffs, width=16, frac_prec=8):
    M = len(b_coeffs) - 1
    N = len(a_coeffs) - 1

    # ================= FIXED-POINT CONVERSION =================
    b_fixed = [real2fix_point(coef, frac_prec) for coef in b_coeffs]
    a_fixed = [real2fix_point(coef, frac_prec) for coef in a_coeffs]

    # ================= COEFFICIENT PARAMETERS =================
    int_bits = width - frac_prec
    coef_width_value = int_bits + frac_prec
    coef_params = f"localparam int N = {frac_prec}; // Fractional precision bits\n"
    coef_params += f"localparam int INT_BITS = {int_bits}; // Integer bits\n"
    coef_params += f"localparam int COEF_WIDTH = INT_BITS + N; // Total coefficient width\n"
    coef_params += "// b coefficients (feedforward)\n"
    for i, b_coef in enumerate(b_fixed):
        coef_params += f"localparam logic signed [COEF_WIDTH-1:0] b{i} = {coef_width_value}'sd{b_coef};\n"
    coef_params += "// a coefficients (feedback)\n"
    for i, a_coef in enumerate(a_fixed):
        coef_params += f"localparam logic signed [COEF_WIDTH-1:0] a{i} = {coef_width_value}'sd{a_coef};\n"

    # ================= REGISTERS =================
    x_regs = "\n".join(
        [f"logic signed [{width-1}:0] x{i};" for i in range(M + 1)]
    )
    y_regs = "\n".join(
        [f"logic signed [{width-1}:0] y{i};" for i in range(1, N + 1)]
    )

    # ================= EXPRESSIONS =================
    ff_terms = " + ".join([f"x{i} * b{i}" for i in range(M + 1)])
    fb_terms = " + ".join([f"y{i} * a{i}" for i in range(1, N + 1)])

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

{coef_params}

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
