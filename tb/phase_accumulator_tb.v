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

    //self-checking: tb keeps its own expected phase and compares every cycle
    reg [31:0] expected;
    integer errors = 0;

    task check;
        begin
            if (phase !== expected) begin
                $display("FAIL t=%0t phase=%h expected=%h", $time, phase, expected);
                errors = errors + 1;
            end
        end
    endtask

    //stimulus -- inputs change on negedge so they are stable at posedge
    initial begin
        rst = 1;
        en  = 0;
        increment = 0;
        expected = 0;

        //reset: phase must be 0
        repeat (2) @(negedge clk);
        check;

        //count by 1
        rst = 0;
        en = 1;
        increment = 1;
        repeat (10) begin
            @(negedge clk);
            expected = expected + increment;
            check;
        end

        //en low: phase must hold
        en = 0;
        repeat (5) begin
            @(negedge clk);
            check;
        end

        //large increment: phase must wrap past 2^32
        en = 1;
        increment = 32'h4000_0000;
        repeat (8) begin
            @(negedge clk);
            expected = expected + increment;
            check;
        end

        //reset mid-run: back to 0
        rst = 1;
        @(negedge clk);
        expected = 0;
        check;

        if (errors == 0) $display("PASS");
        else             $display("FAILED with %0d errors", errors);
        $finish;
    end

    //write to waveform
    initial begin
        $dumpfile("phase_accumulator_tb.vcd");
        $dumpvars(0 , phase_accumulator_tb);
    end

endmodule
