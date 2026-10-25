`timescale 1ns/1ps
`default_nettype none

//Self-checking testbench for midi_uart_rx. A monitor counts every valid and framing_error pulse, so
//checks don't depend on when the pulse happens; each byte's check runs after its stop bit has ended.
//The expected byte is the one handed to send_frame, which sends it LSB first.
module tb_midi_uart_rx(); //no ports on testbench

    //parameters, so run.py can override them with -G
    parameter CLK_FREQ = 100000000;
    parameter BAUD_RATE = 31250;
    parameter DATA_W = 8;

    localparam real CLK_PERIOD_NS = 1.0e9 / CLK_FREQ;
    localparam real BIT_NS = 1.0e9 / BAUD_RATE;        //nominal bit period
    localparam real FAST = 0.97;                       //sender bit period scale: 3% fast / slow baud
    localparam real SLOW = 1.03;
    localparam NUM_RANDOM = 50;                        //bytes per random test

    //reg to DRIVE , wire to READ
    reg clk = 0;
    reg rst = 0;
    reg rx = 1;
    wire [DATA_W-1:0] out;
    wire valid;
    wire framing_error;

    integer errors = 0;
    integer byte_idx = 0;                              //bytes checked so far, for the FAIL messages
    reg [8*12-1:0] test_name = "reset";                //current test, for the FAIL messages

    //instatiate the DUT
    midi_uart_rx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE),
        .DATA_W(DATA_W)
    ) dut (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .out(out),
        .valid(valid),
        .framing_error(framing_error)
    );

    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    //monitor: counts pulses and keeps out from the clock valid was high (out is only meaningful then)
    integer valid_count = 0;
    integer fe_count = 0;
    reg [DATA_W-1:0] last_out = 0;
    always @(posedge clk) begin
        if (valid) begin
            valid_count = valid_count + 1;
            last_out = out;
        end
        if (framing_error)
            fe_count = fe_count + 1;
    end

    task clear_counts;
        begin
            valid_count = 0;
            fe_count = 0;
        end
    endtask

    //compare one value, print a FAIL line in the key=value format run.py expects
    task check_eq(input [8*16-1:0] sig, input integer expected, input integer got);
        begin
            if (expected !== got) begin
                $display("FAIL t=%0d test=%0s byte=%0d sig=%0s expected=%0d got=%0d",
                         $time, test_name, byte_idx, sig, expected, got);
                errors = errors + 1;
            end
        end
    endtask

    //start bit, DATA_W data bits LSB first, then stop_bit; every bit lasts bit_ns
    task send_frame(input [DATA_W-1:0] b, input stop_bit, input real bit_ns);
        integer i;
        begin
            rx = 0;
            #(bit_ns);
            for (i = 0; i < DATA_W; i = i + 1) begin
                rx = b[i];
                #(bit_ns);
            end
            rx = stop_bit;
            #(bit_ns);
        end
    endtask

    //send one good byte and check exactly one valid with that byte and no framing error
    task send_and_check(input [DATA_W-1:0] b, input real bit_ns);
        begin
            clear_counts();
            send_frame(b, 1'b1, bit_ns);
            check_eq("valid_count", 1, valid_count);
            check_eq("fe_count", 0, fe_count);
            check_eq("out", b, last_out);
            byte_idx = byte_idx + 1;
        end
    endtask

    task idle(input real ns);
        begin
            rx = 1;
            #(ns);
        end
    endtask

    //random bytes back to back at a scaled bit period, each started at a random point in the clock
    //cycle so the start edge isn't always in phase with clk
    task random_bytes(input real bit_ns);
        integer n;
        begin
            for (n = 0; n < NUM_RANDOM; n = n + 1) begin
                #(CLK_PERIOD_NS * ($urandom % 100) / 100.0);
                send_and_check($urandom, bit_ns);
            end
        end
    endtask

    //STIMULUS

    initial begin
        //reset, with rx held low (a disconnected or still-booting Teensy): outputs clear,
        //and the line going low then high must not look like a byte
        rst = 1;
        rx = 0;
        repeat (5) @(posedge clk);
        #1;
        check_eq("out", 0, out);
        check_eq("valid", 0, valid);
        check_eq("framing_error", 0, framing_error);
        rst = 0;
        clear_counts();
        #(2 * BIT_NS);
        idle(2 * BIT_NS);
        check_eq("valid_count", 0, valid_count);
        check_eq("fe_count", 0, fe_count);

        //one known byte
        test_name = "one_byte";
        send_and_check(8'b11001010, BIT_NS);
        idle(2 * BIT_NS);

        //framing error: stop bit low gives framing_error and no valid, then the next byte still works
        test_name = "framing";
        clear_counts();
        send_frame(8'b11001011, 1'b0, BIT_NS);
        check_eq("valid_count", 0, valid_count);
        check_eq("fe_count", 1, fe_count);
        byte_idx = byte_idx + 1;
        idle(BIT_NS);
        send_and_check(8'b00110101, BIT_NS);
        idle(2 * BIT_NS);

        //glitch shorter than half a bit: START must see rx high again at mid-bit and go back to IDLE
        test_name = "glitch";
        clear_counts();
        rx = 0;
        #(BIT_NS / 4);
        idle(12 * BIT_NS);
        check_eq("valid_count", 0, valid_count);
        check_eq("fe_count", 0, fe_count);
        send_and_check(8'b10010110, BIT_NS);
        idle(2 * BIT_NS);

        //reset partway through a byte, sender gives up too: no pulse for the cut-off byte, next one works.
        //If reset left the state machine running it would sample the idle-high line as data and stop bit.
        test_name = "mid_reset";
        clear_counts();
        rx = 0;
        #(BIT_NS);
        rx = 1;
        #(3 * BIT_NS);
        @(posedge clk) #1 rst = 1;
        repeat (3) @(posedge clk);
        #1 rst = 0;
        idle(12 * BIT_NS);
        check_eq("valid_count", 0, valid_count);
        check_eq("fe_count", 0, fe_count);
        send_and_check(8'b01011100, BIT_NS);
        idle(2 * BIT_NS);

        //random bytes back to back (no idle between stop and next start) at nominal, fast and slow baud.
        //Contradicts the assumption that the sender's bit period matches CLKS_PER_BIT exactly.
        test_name = "random";
        random_bytes(BIT_NS);
        test_name = "baud_fast";
        random_bytes(BIT_NS * FAST);
        test_name = "baud_slow";
        random_bytes(BIT_NS * SLOW);

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("errors=%0d", errors);
        end
    $finish;
    end
endmodule

`default_nettype wire
