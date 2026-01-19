package signal_gen_pkg();
    timeunit 1ns;
    timeprecision 1ps;

    // Math parameters
    parameter real PI = 3.141592653589793;


    // Sine wave structure
    typedef struct {
        real offset;
        real amp;
        real freq;
        realtime t0;
        real phase;
    } sine_struct;


    // Get sine real value
    function real get_sine_value(input sine_struct s);
        get_sine_value = s.offset + s.amp * $sin(2.0 * PI * s.freq * ($realtime - s.t0) * 1e-9 + s.phase/360.0);
    endfuction

    // Initialize sine structure
    function sine_struct start_sine_signal(input real offset, amp, freq, phase=0.0);
        start_sine_signal.offset = offset;
        start_sine_signal.amp    = amp;
        start_sine_signal.freq   = freq;
        start_sine_signal.t0     = $realtime;
        start_sine_signal.phase  = phase;
    endfuction
    
endpackage
