`timescale 1ns/ 1ps
`default_nettype none

//simple dual-port RAM, one-clock read latency, same-address read and write returns old data, and no reset as BRAM can't.
module ram_1r1w #(
    parameter DATA_W = 32,
    parameter DEPTH = 16,
    localparam ADDR_W = DEPTH <= 1 ? 1 : $clog2(DEPTH)
)(
    //inputs
    input wire clk,                         //clock
    input wire wr_en,                       //write enable writes when equal to 1
    input wire [ADDR_W-1:0] wr_addr,        //entry index, 0 to DEPTH-1
    input wire [ADDR_W-1:0] rd_addr,        //entry index, 0 to DEPTH-1
    input wire [DATA_W-1:0] wr_data,        //DATA_W bits, format defined by user

    //outputs
    output reg [DATA_W-1:0] rd_data         //DATA_W bits, same format as wr_data; mem[rd_addr] one clock after rd_addr.
);

    reg [DATA_W-1:0] mem [DEPTH-1:0];

    always @(posedge clk) begin
        rd_data <= mem[rd_addr];
        if (wr_en)
            mem[wr_addr] <= wr_data;
    end

endmodule

`default_nettype wire
