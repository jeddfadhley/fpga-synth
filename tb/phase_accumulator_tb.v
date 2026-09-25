`timescale 1ns/ 1ps
`default_nettype none

module phase_accumulator_tb;
    //one signal per DUT port
    reg clk;        //driven by tb -> reg
    reg rst;
    reg en;
    reg [32:0] increment;
    wire [32:0] phase; //driven by DUT -> wire

    //connecting the dut to the tb
    phase_accumuator #(.WIDTH(32)) dut (
        .clk (clk),
        .rst (rst),
        .en  (en),
        .increment (increment),
        .phase (phase)
    )

    //100MHz clock
    initial clk <= 0;
    always #5 clk = ~clk;
