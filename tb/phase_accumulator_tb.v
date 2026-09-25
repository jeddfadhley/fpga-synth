`timescale 1ns/ 1ps
`default_nettype none

module phase_accumulator_tb;
    //one signal per DUT port
    reg clk;        //driven by tb -> reg
    reg rst;
    reg en;
    reg [31:0] increment;
    wire [31:0] phase; //driven by DUT -> wire

    //connecting the dut to the tb
    phase_accumulator #(.WIDTH(32)) dut (
        .clk (clk),
        .rst (rst),
        .en  (en),
        .increment (increment),
        .phase (phase)
    );

    //100MHz clock
    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        rst = 1;
        en  = 0;
        increment = 0;
        repeat (2) @(negedge clk);
        $finish;
    end

    //write to waveform
    initial begin
        $dumpfile("phase_accumulator_tb.vcd");
        $dumpvars(0 , phase_accumulator_tb);
    end

endmodule
