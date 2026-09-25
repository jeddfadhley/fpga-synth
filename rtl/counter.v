// counter.v
//
// THROWAWAY MODULE — Phase 0 only.
// Its sole purpose is to prove the toolchain flow (RTL -> Icarus -> cocotb ->
// Python-checked pass). It is NOT part of the synthesiser. Delete it once the
// NCO has a passing testbench of its own.
//
// Free-running counter with active-high synchronous reset and a registered
// output, matching the project naming conventions.

module counter #(
    parameter WIDTH = 8          // counter width in bits
) (
    input  wire             clk, // clock
    input  wire             rst, // active-high synchronous reset
    output reg  [WIDTH-1:0] count // registered count output
);

    always @(posedge clk) begin
        if (rst)
            count <= {WIDTH{1'b0}};
        else
            count <= count + 1'b1; // wraps naturally at 2**WIDTH
    end

endmodule
