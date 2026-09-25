`default_nettype none

module phase_accumulator #(
    parameter WIDTH = 32
) (
    input wire clk,                      //clock
    input wire rst,                      //reset --active high , synchronous
    input wire en,                       //enable -- when en is low phase doesnt increment
    input wire [WIDTH-1:0] increment,
    output reg [WIDTH-1:0] phase
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
