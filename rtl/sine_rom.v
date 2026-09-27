`timescale 1ns/ 1ps
`default_nettype none

//synchronous ROM: sample_output = mem[address_input] one clk after address is sampled
module sine_rom #(
    parameter ADDR_W = 10,
    parameter DATA_W = 16,
    parameter INIT_FILE = "rtl/mem/sine_1024x16.hex"
) (
    input wire clk,                      //clock

    input wire [ADDR_W-1:0] address_input,            //UQ0.ADDR_W: fraction of a cycle, 0 = 0 rad, wraps at 2pi
    output reg signed [DATA_W-1:0] sample_output     // Q1.(DATA_W-1): two's complement, int range +/- (2**(DATA_W-1)-1)

);
    reg signed [DATA_W-1:0] mem [0: (1<<ADDR_W)-1];
    initial $readmemh(INIT_FILE, mem);

    always@(posedge clk) begin
        sample_output <= mem[address_input];
    end

endmodule

`default_nettype wire

