`timescale 1ns/1ps
`default_nettype none

module midi_uart_rx #(
    parameter CLK_FREQ = 100000000,
    parameter BAUD_RATE = 31250,
    parameter DATA_W  = 8
)(
    input wire clk,
    input wire rst,
    input wire rx,
    output reg [DATA_W-1:0] out,
    output reg valid,
    output reg framing_error
);

    //local params
    localparam CLKS_PER_BIT = CLK_FREQ/BAUD_RATE;
    localparam HALF_PER_BIT = CLK_FREQ/(BAUD_RATE * 2);
    localparam CLK_COUNT_W  = $clog2(CLKS_PER_BIT);
    localparam BIT_COUNT_W  = $clog2(DATA_W);
    // terminal counts, sized to their counters so the compares are width-matched.
    // Truncating before the -1 is safe: N-1 always fits in $clog2(N) bits, so the
    // wrap gives the right answer mod 2^W (DATA_W=8: 3'b000 - 1 = 3'b111 = 7).
    localparam [CLK_COUNT_W-1:0] HALF_LAST = HALF_PER_BIT[CLK_COUNT_W-1:0] - 1'b1;
    localparam [CLK_COUNT_W-1:0] BIT_LAST  = CLKS_PER_BIT[CLK_COUNT_W-1:0] - 1'b1;
    localparam [BIT_COUNT_W-1:0] DATA_LAST = DATA_W[BIT_COUNT_W-1:0] - 1'b1;


    //states
    localparam IDLE         = 2'b00;
    localparam START        = 2'b01;
    localparam DATA         = 2'b10;
    localparam STOP         = 2'b11;

    //registers
    reg [1:0] state;
    reg rx_sync;
    reg rx_meta;
    reg rx_prev;

    //counters
    reg [CLK_COUNT_W-1:0] clk_count;
    reg [BIT_COUNT_W-1:0] bit_count;

    always @(posedge clk) begin

        rx_meta <= rx;
        rx_sync <= rx_meta;
        rx_prev <= rx_sync;

        if (rst) begin
            state <= IDLE;
            clk_count <= 0;
            bit_count <= 0;
            out <= 0;
            valid <= 0;
            framing_error <= 0;

        end else begin
            // one-clock pulses: cleared every cycle unless STOP sets them
            valid <= 0;
            framing_error <= 0;

            case (state)
                IDLE: begin
                    if(rx_sync == 0 && rx_prev == 1) begin
                        state <= START;
                        clk_count <= 0;
                        bit_count <= 0;
                    end else begin
                        state <= IDLE;
                    end
                end

                START: begin
                    if (clk_count == HALF_LAST) begin
                        if (rx_sync == 0) begin
                            state <= DATA;
                            clk_count <= 0;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DATA: begin
                    if (clk_count == BIT_LAST) begin
                        if (bit_count == DATA_LAST) begin
                            state <= STOP;
                        end else begin
                            bit_count <= bit_count + 1;
                        end
                        out <= {rx_sync , out[DATA_W-1:1]};
                        clk_count <= 0;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                STOP: begin
                    if (clk_count == BIT_LAST) begin
                        if (rx_sync) begin
                            valid <= 1;
                        end else begin
                            framing_error <= 1;
                        end
                        state <= IDLE;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end
            endcase
        end
    end
endmodule

`default_nettype wire
