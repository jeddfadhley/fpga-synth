`timescale 1ns/ 1ps
`default_nettype none

//I2S transmitter (Philips format) and the synth's sample tick. One frame = left slot then right slot;
//each sample is sent MSB first, one BCLK after LRCLK changes, padded with zeros to SLOT_W bits.
module i2s_tx #(
    parameter BCLK_DIV = 32,                //FPGA clocks per bit; power of two, >= 2
    parameter SLOT_W = 32,                  //bits per channel slot; power of two
    parameter DATA_W = 16                   //bits per sample; <= SLOT_W
)(
    input wire clk,                         //clock
    input wire rst,                         //reset active high -- synchronous
    input wire [DATA_W-1:0] sample_l,       //signed Q1.(DATA_W-1), left channel, captured at tick
    input wire [DATA_W-1:0] sample_r,       //signed Q1.(DATA_W-1), right channel, captured at tick
    output reg i2s_bclk,                    //bit clock: low for the first half of each bit, high for the second
    output reg i2s_lrclk,                   //0 while sending the left sample, 1 while sending the right
    output reg i2s_data,                    //data bits, one per BCLK, MSB first; changes on BCLK falling edge
    output reg tick                         //1-clock pulse every BCLK_DIV*2*SLOT_W clocks: samples have been captured
);
    localparam FRAME_CLKS = BCLK_DIV * 2 * SLOT_W;                  //clocks in one frame
    localparam COUNTER_W = $clog2(FRAME_CLKS);                      //bits to count 0 .. FRAME_CLKS-1
    localparam BIT_POS_W = $clog2(BCLK_DIV);                        //bits to count 0 .. BCLK_DIV-1
    localparam SLOT_POS_W = $clog2(SLOT_W);                         //bits to count 0 .. SLOT_W-1
    localparam [COUNTER_W-1:0] LAST = COUNTER_W'(FRAME_CLKS-1);     //last count of the frame

    reg [COUNTER_W-1:0] counter;            //position in the frame, 0 .. FRAME_CLKS-1
    reg [DATA_W-1:0] held_l;                //signed Q1.(DATA_W-1), snapshot of sample_l taken at tick
    reg [DATA_W-1:0] held_r;                //signed Q1.(DATA_W-1), snapshot of sample_r taken at tick
    reg [SLOT_W-1:0] shift_reg;             //bits of the current slot; front = [SLOT_W-1]

    //counter = {left/right, slot_pos, bit_pos}
    wire [BIT_POS_W-1:0] bit_pos = counter[BIT_POS_W-1:0];                  //position inside the current bit, 0 .. BCLK_DIV-1
    wire [SLOT_POS_W-1:0] slot_pos = counter[BIT_POS_W +: SLOT_POS_W];      //which bit of the slot, 0 .. SLOT_W-1
    wire [SLOT_W-1:0] word = counter[COUNTER_W-1] ? {held_r, {(SLOT_W-DATA_W){1'b0}}}
                                                  : {held_l, {(SLOT_W-DATA_W){1'b0}}};  //slot to load: sample for this half then padding zeros

    //frame counter, tick and sample capture, BCLK and LRCLK
    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            tick <= 0;
            held_l <= 0;
            held_r <= 0;
            i2s_bclk <= 0;
            i2s_lrclk <= 0;
        end else if (counter == LAST) begin
            tick <= 1;
            held_l <= sample_l;
            held_r <= sample_r;
            counter <= 0;
            i2s_bclk <= bit_pos[BIT_POS_W-1];
            i2s_lrclk <= counter[COUNTER_W-1];
        end else begin
            counter <= counter + 1;
            tick <= 0;
            i2s_bclk <= bit_pos[BIT_POS_W-1];
            i2s_lrclk <= counter[COUNTER_W-1];
        end
    end

    //data: at the start of each bit send the front of shift_reg, then load a new slot (slot_pos 0) or shift.
    //Loading at slot_pos 0 while sending the old front bit gives the one-BCLK delay after LRCLK changes.
    always @(posedge clk) begin
        if (rst) begin
            shift_reg <= 0;
            i2s_data <= 0;
        end else if (bit_pos == 0) begin
            i2s_data <= shift_reg[SLOT_W-1];
            if (slot_pos == 0) begin
                shift_reg <= word;
            end else begin
                shift_reg <= shift_reg << 1;
            end
        end
    end

endmodule

`default_nettype wire
