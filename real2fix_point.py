
def main():
    real = 0.4375 # sample value
    n = 12 # sample value
    fix_point = real2fix_point(real, n)
    print('real value =', real, '\nfix point  =', fix_point)

def real2fix_point(real, n):
    # Val - value to convert
    # n   - fractional precision
    scaling_factor = 2 ** n # scaling factor
    scaled_val = real * scaling_factor # scaled value
    fix_point = int(round(scaled_val)) # round + cast to int
    return fix_point

if __name__ == '__main__':
    main()


# ------------------ NOTES ------------------
'''
    In systemVerilog you would assign decimal fixed point in the following way:

        localparam int N = 16; // sample bit width
        logic signed [N-1:0] coef = N'd<fixed_point>

    Because in fixed point we will be using N bits, and the fractional precision that we use is n bits, this means
    that we will be using N-n bits for integer value and n bits for fractional value
    '''