`timescale 1ns/ 1ps
`default_nettype none

module phase_accumulator #(
    parameter WIDTH = 32
) (
    input wire clk,                      //clock
    input wire rst,                      //reset --active high , synchronous
    input wire en,                       //enable -- when en is low phase doesnt increment
    input wire [WIDTH-1:0] increment,    //UQ0.WIDTH, fraction of a cycle added per clk
    output reg [WIDTH-1:0] phase         //UQ0.WIDTH, 0 = start of cycles, wraps at 1.0
);
    always @(posedge clk) begin
        if (rst) begin
            phase <= {WIDTH{1'b0}};
        end else if (en) begin
            phase <= phase + increment;
        end
    end

endmodule

`default_nettype wire
