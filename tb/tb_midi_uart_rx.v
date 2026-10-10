`timescale 1ns/1ps
`default_nettype none

module tb_midi_uart_rx(); //no ports on testbench

    localparam CLK_FREQ = 100000000;
    localparam BAUD_RATE = 31250;
    localparam DATA_W = 8;
    localparam CLKS_PER_BIT = CLK_FREQ/BAUD_RATE;
    localparam HALF_PER_BIT = CLK_FREQ/(BAUD_RATE * 2);

    //reg to DRIVE , wire to READ
    reg clk = 0;
    reg rst = 0;
    reg rx = 1;
    wire [DATA_W-1:0] out;
    wire valid;
    wire framing_error;

    integer errors = 0;

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

    //setup clock to flip every 5ns total period: 10ns
    always #5 clk = ~clk;

    //reuasable check taking in 3 inputs and checking count and tc
    task check(input [DATA_W-1:0] out_expected , input valid_expected, input framing_expected);  // name is "check", it takes 3 inputs
        begin
            if(out !== out_expected || valid !== valid_expected || framing_error !== framing_expected) begin
                $display("fail at %0t: out = %0b out_expected = %0b valid= %0b valid_expected = %0b framing error= %0b framing_expected = %0b",
                $time, out, out_expected, valid, valid_expected, framing_error, framing_expected);
                errors = errors + 1;
            end
        end
    endtask

    //reuasable send byte task
    task send_byte(input [DATA_W-1:0] sent_byte);
        begin
            rx = 0;//start bit
            #32000;
            rx = sent_byte[0]; //bit 1
            #32000;
            rx = sent_byte[1]; //bit 2
            #32000;
            rx = sent_byte[2]; //bit 3
            #32000;
            rx = sent_byte[3]; //bit 4
            #32000;
            rx = sent_byte[4]; //bit 5
            #32000;
            rx = sent_byte[5]; //bit 6
            #32000;
            rx = sent_byte[6]; //bit 7
            #32000;
            rx = sent_byte[7]; //bit 8
            #32000;
            rx = 1; //stop bit
            #32000;
        end
    endtask

    //STIMULUS

    initial begin
        //test 1 -- RESET
        rst = 1;
        @(posedge clk) #1;
        check(8'b00000000, 0,0);
        @(posedge clk) #1;
        rst = 0;


        //test 2 -- SENDING A BYTE
        send_byte(8'b11001010);
        check(8'b11001010, 1, 0);

        #64000;

        //test 3 framing error
        rx = 0; //start bit
        #32000;
        rx = 1; //bit 1
        #32000;
        rx = 1; //bit 2
        #32000;
        rx = 0; //bit 3
        #32000;
        rx = 1; //bit 4
        #32000;
        rx = 0; //bit 5
        #32000;
        rx = 0; //bit 6
        #32000;
        rx = 1; //bit 7
        #32000;
        rx = 1; //bit 8
        #32000;
        rx = 0; //stop bit
        #32000;
        check(8'b11001011, 0, 1);
        rx= 1;
        #32000;

        //test 4 sending multiple bytes
        send_byte(8'b11001010);
        check(8'b11001010, 1, 0);
        send_byte(8'b11101010);
        check(8'b11101010, 1, 0);
        send_byte(8'b11011010);
        check(8'b11011010, 1, 0);
        send_byte(8'b11111111);
        check(8'b11111111, 1, 0);
        send_byte(8'b11111010);
        check(8'b11111010, 1, 0);
        send_byte(8'b11000000);
        check(8'b11000000, 1, 0);

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("errors = %0d ", errors);
        end
    $finish;
    end
endmodule