`timescale 1ns/1ps
`default_nettype none

//mono oscillator: phase_accumulator feeding sine_rom. sample = sine of the phase's top ADDR_W bits,
//2 clocks after en (accumulator register, then ROM register). f_out = increment * fs / 2**PHASE_W.
module nco #(
    parameter PHASE_W = 32,                             //phase accumulator bits; sets frequency resolution
    parameter ADDR_W = 10,                              //sine table address bits; <= PHASE_W
    parameter DATA_W = 16,                              //sample bits
    parameter INIT_FILE = "rtl/mem/sine_1024x16.hex"    //sine table, 2**ADDR_W entries of DATA_W bits
)(
    input wire clk,                                     //clock
    input wire rst,                                     //reset active high -- synchronous; resets the phase and sample_valid, not the ROM
    input wire en,                                      //advance one sample: the i2s_tx tick
    input wire [PHASE_W-1:0] increment,                 //UQ0.PHASE_W, fraction of a cycle added per en
    output wire signed [DATA_W-1:0] sample,             //Q1.(DATA_W-1), sine of the phase, 2 clocks after en
    output reg sample_valid                             //1 for the clock in which a new sample first appears
);

    //low PHASE_W-ADDR_W bits are the fine phase: they set frequency resolution but are
    //deliberately dropped at the ROM address (phase truncation)
    /* verilator lint_off UNUSEDSIGNAL */
    wire [PHASE_W-1:0] phase_out_acc;                   //UQ0.PHASE_W, current phase
    /* verilator lint_on UNUSEDSIGNAL */
    reg valid_dly;                                      //en delayed 1 clock, lines up with phase_out_acc

    phase_accumulator #(
        .WIDTH(PHASE_W)
    ) phase_accumulator0 (
        .clk(clk),
        .rst(rst),
        .en(en),
        .increment(increment),
        .phase(phase_out_acc)
    );

    sine_rom #(
        .ADDR_W(ADDR_W),
        .DATA_W(DATA_W),
        .INIT_FILE(INIT_FILE)
    ) sine_rom0 (
        .clk(clk),
        .address_input(phase_out_acc[PHASE_W-1 -: ADDR_W]),
        .sample_output(sample)
    );

    //en through two registers, matching the accumulator and ROM registers on the sample path
    always @(posedge clk) begin
        if (rst) begin
            valid_dly <= 0;
            sample_valid <= 0;
        end else begin
            valid_dly <= en;
            sample_valid <= valid_dly;
        end
    end

endmodule

`default_nettype wire
