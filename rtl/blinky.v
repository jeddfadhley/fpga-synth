`timescale 1ns/ 1ps
`default_nettype none

//program to blink an LED on a basys 3 FPGA
module blinky #(
    parameter CLK_HZ = 100000000,
    parameter BLINK_HZ = 1,
    localparam HALF_PERIOD = CLK_HZ / (2* BLINK_HZ),
    /* verilator lint_off WIDTHTRUNC */ //HALF_PERIOD-1 alwyas fits in COUNT_W bits
    localparam [COUNT_W-1:0] LAST = HALF_PERIOD - 1,
    /* verilator lint_on WIDTHTRUNC */
    localparam COUNT_W = $clog2(HALF_PERIOD)


)(
    input wire clk,
    input wire rst,
    output wire [0:0] led

);

    reg led_state;
    reg [COUNT_W-1:0] count;
    assign led[0] = led_state;

    always@(posedge clk) begin
        if (rst) begin
            count <= 0;
            led_state <= 0;
        end else begin

            count <= count + 1;

            if (count == LAST) begin
                led_state <= ~led_state;
                count <= 0;
            end
        end
    end
endmodule

`default_nettype wire




