// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

bool Vtop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__ico\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

extern const VlWide<16>/*511:0*/ Vtop__ConstPool__CONST_hafc400eb_0;
extern const VlUnpacked<CData/*3:0*/, 64> Vtop__ConstPool__TABLE_h0217b6c6_0;
extern const VlUnpacked<CData/*2:0*/, 128> Vtop__ConstPool__TABLE_hf33c53e0_0;
extern const VlUnpacked<CData/*0:0*/, 128> Vtop__ConstPool__TABLE_h312b9a0c_0;

void Vtop___024root___ico_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ico_sequent__TOP__0\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VdfgRegularize_h6e95ff9d_0_2;
    __VdfgRegularize_h6e95ff9d_0_2 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_4;
    __VdfgRegularize_h6e95ff9d_0_4 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_5;
    __VdfgRegularize_h6e95ff9d_0_5 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_10;
    __VdfgRegularize_h6e95ff9d_0_10 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_11;
    __VdfgRegularize_h6e95ff9d_0_11 = 0;
    CData/*3:0*/ __VdfgRegularize_h6e95ff9d_0_13;
    __VdfgRegularize_h6e95ff9d_0_13 = 0;
    // Body
    vlSelfRef.processorci_top__DOT__imem_prog_we = vlSelfRef.imem_prog_we;
    vlSelfRef.processorci_top__DOT__imem_prog_addr 
        = vlSelfRef.imem_prog_addr;
    vlSelfRef.processorci_top__DOT__imem_prog_data 
        = vlSelfRef.imem_prog_data;
    vlSelfRef.processorci_top__DOT__dmem_prog_we = vlSelfRef.dmem_prog_we;
    vlSelfRef.processorci_top__DOT__dmem_prog_addr 
        = vlSelfRef.dmem_prog_addr;
    vlSelfRef.processorci_top__DOT__dmem_prog_data 
        = vlSelfRef.dmem_prog_data;
    vlSelfRef.processorci_top__DOT__core_data_in = vlSelfRef.core_data_in;
    vlSelfRef.processorci_top__DOT__core_ack = vlSelfRef.core_ack;
    vlSelfRef.processorci_top__DOT__data_mem_data_in 
        = vlSelfRef.data_mem_data_in;
    vlSelfRef.processorci_top__DOT__data_mem_ack = vlSelfRef.data_mem_ack;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
    vlSelfRef.processorci_top__DOT__rst_n = vlSelfRef.rst_n;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br;
    vlSelfRef.processorci_top__DOT__sys_clk = vlSelfRef.sys_clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__syn_rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__wb_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__r_data_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__rdata;
    vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__rdata;
    vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__wb_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_rd;
    vlSelfRef.processorci_top__DOT___core_data_in = vlSelfRef.processorci_top__DOT__core_data_in;
    vlSelfRef.processorci_top__DOT___core_ack = vlSelfRef.processorci_top__DOT__core_ack;
    vlSelfRef.processorci_top__DOT___data_mem_data_in 
        = vlSelfRef.processorci_top__DOT__data_mem_data_in;
    vlSelfRef.processorci_top__DOT___data_mem_ack = vlSelfRef.processorci_top__DOT__data_mem_ack;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_pc;
    vlSelfRef.processorci_top__DOT__rst_core = (1U 
                                                & (~ (IData)(vlSelfRef.processorci_top__DOT__rst_n)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br_addr_mode;
    vlSelfRef.processorci_top__DOT__imem_fetch_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__if_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br;
    vlSelfRef.processorci_top__DOT__clk_core = vlSelfRef.processorci_top__DOT__sys_clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__syn_rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__r_data_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__r_data_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_en 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__sys_rstn 
        = (1U & (~ (IData)(vlSelfRef.processorci_top__DOT__rst_core)));
    vlSelfRef.imem_fetch_addr = vlSelfRef.processorci_top__DOT__imem_fetch_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__if_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr_2 
        = (0x00000fffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr 
                          >> 2U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__sys_clk 
        = vlSelfRef.processorci_top__DOT__clk_core;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT____Vstrobe0 = 1U;
        vlSelfRef.processorci_top__DOT__adam_mem_we = 1U;
    } else {
        vlSelfRef.processorci_top__DOT__adam_mem_we = 0U;
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write) 
           | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_read));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__r_data_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_en;
    vlSelfRef.processorci_top__DOT__Processor__DOT__if_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_inst;
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6 = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_regs_write) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb 
        = (3U & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_mem2reg) 
           & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_mem_write) 
              & ((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
                 & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rs2)))));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7 = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_regs_write) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__sys_rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr_2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__sys_clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_ctrl_r 
        = (0x0000000fU & ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                           ? (0x0dU | ((- (IData)((1U 
                                                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op)))) 
                                       | (- (IData)(
                                                    (1U 
                                                     & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op) 
                                                        >> 1U))))))
                           : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                               ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                                   ? ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                       ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                           ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? 7U
                                               : 8U)
                                           : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)
                                                   ? 4U
                                                   : 3U)
                                               : 9U))
                                       : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                           ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? 6U
                                               : 5U)
                                           : ((- (IData)(
                                                         (1U 
                                                          & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code)))) 
                                              & (2U 
                                                 | (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)))))))
                                   : Vtop__ConstPool__CONST_hafc400eb_0
                                  [((0x07fffffeU & 
                                     ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code) 
                                      << 1U)) | (0x07ffffffU 
                                                 & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)))])
                               : ((0xc6b5ffa1U >> ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code) 
                                                   << 2U)) 
                                  & (- (IData)((1U 
                                                & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn;
    vlSelfRef.processorci_top__DOT__core_we = vlSelfRef.processorci_top__DOT__adam_mem_we;
    vlSelfRef.processorci_top__DOT__data_mem_we = vlSelfRef.processorci_top__DOT__adam_mem_we;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__en_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_en = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_addr = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word 
        = (3U & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem);
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__if_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3 = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__alu_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_ctrl_r;
    vlSelfRef.core_we = vlSelfRef.processorci_top__DOT__core_we;
    vlSelfRef.data_mem_we = vlSelfRef.processorci_top__DOT__data_mem_we;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__en_mem;
    vlSelfRef.processorci_top__DOT__core_cyc = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__core_stb = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__data_mem_cyc = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__data_mem_stb = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem_2 
        = (0x00000fffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem 
                          >> 2U));
    vlSelfRef.processorci_top__DOT__adam_bus_addr = 
        (0x7fffffffU & vlSelfRef.processorci_top__DOT__adam_mem_addr);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem 
        = Vtop__ConstPool__TABLE_h0217b6c6_0[(((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word) 
                                               << 4U) 
                                              | (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code) 
                                                  << 1U) 
                                                 | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write)))];
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__inst_swift)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst_reg
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst);
    vlSelfRef.processorci_top__DOT__Processor__DOT__forward_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b)
            ? 2U : (1U & (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a)
            ? 2U : (1U & (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__alu_ctrl;
    vlSelfRef.core_cyc = vlSelfRef.processorci_top__DOT__core_cyc;
    vlSelfRef.core_stb = vlSelfRef.processorci_top__DOT__core_stb;
    vlSelfRef.data_mem_cyc = vlSelfRef.processorci_top__DOT__data_mem_cyc;
    vlSelfRef.data_mem_stb = vlSelfRef.processorci_top__DOT__data_mem_stb;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem_2;
    vlSelfRef.processorci_top__DOT__core_addr = vlSelfRef.processorci_top__DOT__adam_bus_addr;
    vlSelfRef.processorci_top__DOT__data_mem_addr = vlSelfRef.processorci_top__DOT__adam_bus_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_en_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_wstrb 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem_data;
    VL_WRITEF_NX("wb_mem_data  : %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data);
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__forward_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__forward_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__forwardB 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB;
    if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA))))) {
        VL_WRITEF_NX("forwardA! ex_hazard: %b, mem_hazard: %b\n",2
                     , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a
                     , '#',1,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a));
    } else if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB))))) {
        VL_WRITEF_NX("forwardB! ex_hazard: %b, mem_hazard: %b\n",2
                     , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b
                     , '#',1,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b));
    } else if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data))) {
        VL_WRITEF_NX("forward4store! hazard_data: %b\n",1
                     , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem);
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__forwardA 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__clk;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__clk;
    vlSelfRef.core_addr = vlSelfRef.processorci_top__DOT__core_addr;
    vlSelfRef.data_mem_addr = vlSelfRef.processorci_top__DOT__data_mem_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_en_mem;
    __VdfgRegularize_h6e95ff9d_0_13 = (0x0000000fU 
                                       & ((IData)(vlSelfRef.processorci_top__DOT__adam_mem_wstrb) 
                                          | (- (IData)(
                                                       (1U 
                                                        & (~ (IData)(vlSelfRef.processorci_top__DOT__adam_mem_we)))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__forwardB;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__forwardA;
    vlSelfRef.processorci_top__DOT__core_sel = __VdfgRegularize_h6e95ff9d_0_13;
    vlSelfRef.processorci_top__DOT__data_mem_sel = __VdfgRegularize_h6e95ff9d_0_13;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func3_code 
        = (7U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                 >> 0x0000000cU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func7_code 
        = (1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                 >> 0x0000001eU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rd 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 7U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x0000000fU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x00000014U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs1 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x0000000fU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs2 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x00000014U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op 
        = (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst);
    vlSelfRef.core_sel = vlSelfRef.processorci_top__DOT__core_sel;
    vlSelfRef.data_mem_sel = vlSelfRef.processorci_top__DOT__data_mem_sel;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o 
        = ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
            ? (0x0000ffffU & ((- (IData)((1U & (~ ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code) 
                                                   >> 1U))))) 
                              & ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                                  ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                      ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                         >> 0x00000010U)
                                      : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)
                                  : (0x000000ffU & 
                                     ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                       ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                           ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                              >> 0x00000018U)
                                           : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                              >> 0x00000010U))
                                       : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                           ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                              >> 8U)
                                           : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data))))))
            : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                   & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))))))
                : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                    ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                        ? (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                        >> 0x0000001fU))) 
                            << 0x00000010U) | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                               >> 0x00000010U))
                        : (((- (IData)((1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                              >> 0x0000000fU)))) 
                            << 0x00000010U) | (0x0000ffffU 
                                               & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)))
                    : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                        ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                            ? (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                            >> 0x0000001fU))) 
                                << 8U) | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                          >> 0x00000018U))
                            : (((- (IData)((1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 0x00000017U)))) 
                                << 8U) | (0x000000ffU 
                                          & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                             >> 0x00000010U))))
                        : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                            ? (((- (IData)((1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 0x0000000fU)))) 
                                << 8U) | (0x000000ffU 
                                          & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                             >> 8U)))
                            : (((- (IData)((1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 7U)))) 
                                << 8U) | (0x000000ffU 
                                          & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)))))));
    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe0 = 1U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe1 = 1U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o;
    } else {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o;
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rd;
    if (VL_UNLIKELY(((0x63U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))))) {
        VL_WRITEF_NX("imm_branch : %d\n",1, '#',32,
                     (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                   >> 0x1fU))) << 0x0000000cU) 
                      | ((0x00000800U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                         << 4U)) | 
                         ((0x000007e0U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                          >> 0x00000014U)) 
                          | (0x0000001eU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                            >> 7U))))));
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__imm_o 
        = (((3U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
            | ((0x13U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
               | (0x67U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))))
            ? (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                            >> 0x0000001fU))) << 0x0000000cU) 
               | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                  >> 0x00000014U)) : ((0x23U == (0x0000007fU 
                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))
                                       ? (((- (IData)(
                                                      (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                       >> 0x0000001fU))) 
                                           << 0x0000000cU) 
                                          | ((0x00000fe0U 
                                              & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                 >> 0x00000014U)) 
                                             | (0x0000001fU 
                                                & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                   >> 7U))))
                                       : ((0x63U == 
                                           (0x0000007fU 
                                            & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))
                                           ? (((- (IData)(
                                                          (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                           >> 0x0000001fU))) 
                                               << 0x0000000cU) 
                                              | ((0x00000800U 
                                                  & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                     << 4U)) 
                                                 | ((0x000007e0U 
                                                     & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                        >> 0x00000014U)) 
                                                    | (0x0000001eU 
                                                       & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                          >> 7U)))))
                                           : (((0x37U 
                                                == 
                                                (0x0000007fU 
                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
                                               | (0x17U 
                                                  == 
                                                  (0x0000007fU 
                                                   & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)))
                                               ? (0xfffff000U 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)
                                               : ((
                                                   ((- (IData)(
                                                               (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                                >> 0x0000001fU))) 
                                                    << 0x00000014U) 
                                                   | ((((0x000001feU 
                                                         & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                            >> 0x0000000bU)) 
                                                        | (1U 
                                                           & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                              >> 0x00000014U))) 
                                                       << 0x0000000bU) 
                                                      | (0x000007feU 
                                                         & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                            >> 0x00000014U)))) 
                                                  & (- (IData)(
                                                               (0x6fU 
                                                                == 
                                                                (0x0000007fU 
                                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)))))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_a 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_b 
        = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2) 
            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3));
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_read 
        = (3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br_addr_mode 
        = (0x67U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_op 
        = Vtop__ConstPool__TABLE_hf33c53e0_0[vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op];
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write 
        = Vtop__ConstPool__TABLE_h312b9a0c_0[vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op];
    __VdfgRegularize_h6e95ff9d_0_2 = ((0x67U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                                      | (0x6fU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_write 
        = (0x23U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__imm_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem2reg 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write) 
           & (3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br 
        = ((0x63U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
           | (IData)(__VdfgRegularize_h6e95ff9d_0_2));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src1 
        = (((0x17U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
            | (IData)(__VdfgRegularize_h6e95ff9d_0_2))
            ? 2U : (1U & (- (IData)((0x37U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src2 
        = (((3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
            | ((0x23U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
               | ((0x17U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                  | ((0x37U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                     | (0x13U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op))))))
            ? 1U : (2U & (- (IData)((IData)(__VdfgRegularize_h6e95ff9d_0_2)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_imm;
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8 = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs2) 
                                                == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_regs_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__load_stall 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read) 
           & ((IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8) 
              | ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs1) 
                 == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write_forward;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__forward_data)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_regs_data
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_regs_data2);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_data;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o
            : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))
                ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data
                : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o
            : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))
                ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data
                : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data1));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write_forward;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem 
        = ((0U == (3U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code)))
            ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                ? (((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                     ? (0x0000ff00U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                                       << 8U)) : (0x000000ffU 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre)) 
                   << 0x00000010U) : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                                       ? (0x0000ff00U 
                                          & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                                             << 8U))
                                       : (0x000000ffU 
                                          & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre)))
            : ((1U == (3U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code)))
                ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                    ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                       << 0x00000010U) : (0x0000ffffU 
                                          & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre))
                : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                   & (- (IData)((2U == (3U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code))))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o1 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_a)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank
           [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1]);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o2 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_b)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank
           [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2]);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2))
            ? 4U : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2))
                     ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm
                     : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_addr_op_A 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br_addr_mode)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A 
        = (((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1))
             ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc
             : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre) 
           & (- (IData)((1U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__stall 
        = ((~ ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read) 
               & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_mem_write_forward) 
                  & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8)))) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__load_stall));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_data_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_wdata 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_pc 
        = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm 
           + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_addr_op_A);
    if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))))) {
        VL_WRITEF_NX("forwardA! OP_A: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A);
    } else if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))))) {
        VL_WRITEF_NX("forwardB! OP_B: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B);
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A;
    vlSelfRef.processorci_top__DOT__Processor__DOT__stall 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__stall;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_data_mem;
    vlSelfRef.processorci_top__DOT__core_data_out = vlSelfRef.processorci_top__DOT__adam_mem_wdata;
    vlSelfRef.processorci_top__DOT__data_mem_data_out 
        = vlSelfRef.processorci_top__DOT__adam_mem_wdata;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_pc;
    __VdfgRegularize_h6e95ff9d_0_4 = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                      + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B);
    __VdfgRegularize_h6e95ff9d_0_5 = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                      - vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B);
    __VdfgRegularize_h6e95ff9d_0_10 = (1U & (- (IData)(
                                                       VL_LTS_III(32, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))));
    __VdfgRegularize_h6e95ff9d_0_11 = (1U & (- (IData)(
                                                       (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                                        < vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_stall 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__pc_stall 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_stall 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
    vlSelfRef.core_data_out = vlSelfRef.processorci_top__DOT__core_data_out;
    vlSelfRef.data_mem_data_out = vlSelfRef.processorci_top__DOT__data_mem_data_out;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o 
        = ((8U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
            ? ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                ? (((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                     ? __VdfgRegularize_h6e95ff9d_0_4
                     : __VdfgRegularize_h6e95ff9d_0_11) 
                   & (- (IData)((1U & (~ ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl) 
                                          >> 1U))))))
                : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_10
                        : __VdfgRegularize_h6e95ff9d_0_5)
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           ^ vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)
                        : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           | vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))))
            : ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)
                        : __VdfgRegularize_h6e95ff9d_0_11)
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_10
                        : VL_SHIFTRS_III(32,32,5, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A, 
                                         (0x0000001fU 
                                          & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))))
                : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           >> (0x0000001fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))
                        : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           << (0x0000001fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)))
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_5
                        : __VdfgRegularize_h6e95ff9d_0_4))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_stall 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__pc_stall;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve 
        = (1U & ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn)) 
                 | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_stall)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__br_mark 
        = ((0x0dU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
           | (((0x0aU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
               | ((5U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
                  | (6U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))))
               ? (0U != vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o)
               : (0U == vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_read 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_read));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem2reg 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem2reg));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_op 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_op) 
           & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src1 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src1) 
           & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src2 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src2) 
           & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br_addr_mode 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br_addr_mode));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_write 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__regs_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_mark 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__br_mark;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_ctrl 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_mark));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__rstn 
        = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_flush)) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__cs 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__rstn;
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtop___024root___eval_phase__ico(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__ico\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__ico
        vlSelfRef.__VicoTriggered[0U] = ((0xfffffffffffffffeULL 
                                          & vlSelfRef.__VicoTriggered[0U]) 
                                         | (IData)((IData)(vlSelfRef.__VicoFirstIteration)));
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    __VicoExecute = Vtop___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        {
            // Inlined CFunc: _eval_ico
            if ((1ULL & vlSelfRef.__VicoTriggered[0U])) {
                Vtop___024root___ico_sequent__TOP__0(vlSelf);
            }
        }
    }
    return (__VicoExecute);
}

bool Vtop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void Vtop___024root___nba_sequent__TOP__3(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_sequent__TOP__3\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0;
    __VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 = 0;
    CData/*4:0*/ __VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0;
    __VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 = 0;
    CData/*0:0*/ __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0;
    __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 = 0;
    CData/*0:0*/ __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v1;
    __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v1 = 0;
    // Body
    __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 = 0U;
    __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v1 = 0U;
    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn) {
        if (VL_UNLIKELY((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en) 
                          & (0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)))))) {
            VL_WRITEF_NX("WRITE REGISTER FILE: x%d = %h\n",2
                         , '#',5,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr
                         , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data);
            __VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data;
            __VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr;
            __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0 = 1U;
        }
    } else {
        __VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v1 = 1U;
    }
    if (__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0] 
            = __VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v0;
    }
    if (__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank__v1) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[0U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[1U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[2U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[3U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[4U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[5U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[6U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[7U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[8U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[9U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[10U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[11U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[12U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[13U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[14U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[15U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[16U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[17U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[18U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[19U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[20U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[21U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[22U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[23U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[24U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[25U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[26U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[27U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[28U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[29U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[30U] = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[31U] = 0U;
    }
}

void Vtop___024root___nba_sequent__TOP__5(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_sequent__TOP__5\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*3:0*/ __VdfgRegularize_h6e95ff9d_0_13;
    __VdfgRegularize_h6e95ff9d_0_13 = 0;
    // Body
    VL_WRITEF_NX("me_alu_o: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem2reg 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem2reg));
    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_data2 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_data2;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_func3_code 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_func3_code;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rs2 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rs2;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rd 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rd;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_alu_o;
    } else {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_data2 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_func3_code = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rs2 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rd = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o = 0U;
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_read 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_read));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_write 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_write 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT____Vstrobe0 = 1U;
        vlSelfRef.processorci_top__DOT__adam_mem_we = 1U;
    } else {
        vlSelfRef.processorci_top__DOT__adam_mem_we = 0U;
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write) 
           | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_read));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6 = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_regs_write) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_alu_o;
    vlSelfRef.processorci_top__DOT__core_we = vlSelfRef.processorci_top__DOT__adam_mem_we;
    vlSelfRef.processorci_top__DOT__data_mem_we = vlSelfRef.processorci_top__DOT__adam_mem_we;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__en_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_en = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_addr = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word 
        = (3U & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem);
    vlSelfRef.core_we = vlSelfRef.processorci_top__DOT__core_we;
    vlSelfRef.data_mem_we = vlSelfRef.processorci_top__DOT__data_mem_we;
    vlSelfRef.processorci_top__DOT__core_cyc = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__core_stb = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__data_mem_cyc = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__data_mem_stb = vlSelfRef.processorci_top__DOT__adam_mem_en;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem_2 
        = (0x00000fffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem 
                          >> 2U));
    vlSelfRef.processorci_top__DOT__adam_bus_addr = 
        (0x7fffffffU & vlSelfRef.processorci_top__DOT__adam_mem_addr);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem 
        = Vtop__ConstPool__TABLE_h0217b6c6_0[(((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word) 
                                               << 4U) 
                                              | (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code) 
                                                  << 1U) 
                                                 | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write)))];
    vlSelfRef.core_cyc = vlSelfRef.processorci_top__DOT__core_cyc;
    vlSelfRef.core_stb = vlSelfRef.processorci_top__DOT__core_stb;
    vlSelfRef.data_mem_cyc = vlSelfRef.processorci_top__DOT__data_mem_cyc;
    vlSelfRef.data_mem_stb = vlSelfRef.processorci_top__DOT__data_mem_stb;
    vlSelfRef.processorci_top__DOT__core_addr = vlSelfRef.processorci_top__DOT__adam_bus_addr;
    vlSelfRef.processorci_top__DOT__data_mem_addr = vlSelfRef.processorci_top__DOT__adam_bus_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_en_mem 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem;
    vlSelfRef.processorci_top__DOT__adam_mem_wstrb 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem;
    vlSelfRef.core_addr = vlSelfRef.processorci_top__DOT__core_addr;
    vlSelfRef.data_mem_addr = vlSelfRef.processorci_top__DOT__data_mem_addr;
    __VdfgRegularize_h6e95ff9d_0_13 = (0x0000000fU 
                                       & ((IData)(vlSelfRef.processorci_top__DOT__adam_mem_wstrb) 
                                          | (- (IData)(
                                                       (1U 
                                                        & (~ (IData)(vlSelfRef.processorci_top__DOT__adam_mem_we)))))));
    vlSelfRef.processorci_top__DOT__core_sel = __VdfgRegularize_h6e95ff9d_0_13;
    vlSelfRef.processorci_top__DOT__data_mem_sel = __VdfgRegularize_h6e95ff9d_0_13;
    vlSelfRef.core_sel = vlSelfRef.processorci_top__DOT__core_sel;
    vlSelfRef.data_mem_sel = vlSelfRef.processorci_top__DOT__data_mem_sel;
}

void Vtop___024root___nba_sequent__TOP__6(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_sequent__TOP__6\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VL_WRITEF_NX("ex_regs_data1: %h\nex_regs_data2: %h\nex_imm: %h\nex_alu_op: %h\n",4
                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1
                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2
                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm
                 , '#',3,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_write 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem2reg 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem2reg));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_write 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_write));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br_addr_mode 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br_addr_mode));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func7_code 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func7_code));
    if ((1U & ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
               | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func3_code = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src1 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src2 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_pc = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rd = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs2 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs1 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2 = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1 = 0U;
    } else {
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func3_code 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func3_code;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src1 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src1;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src2 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src2;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_pc 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_pc;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rd 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rd;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs2 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs2;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs1 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs1;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_op;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_imm;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data2;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data1;
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_read 
        = ((1U & (~ ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                     | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush)))) 
           && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_read));
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_pc;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_ctrl_r 
        = (0x0000000fU & ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                           ? (0x0dU | ((- (IData)((1U 
                                                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op)))) 
                                       | (- (IData)(
                                                    (1U 
                                                     & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op) 
                                                        >> 1U))))))
                           : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                               ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))
                                   ? ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                       ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                           ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? 7U
                                               : 8U)
                                           : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)
                                                   ? 4U
                                                   : 3U)
                                               : 9U))
                                       : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                           ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code))
                                               ? 6U
                                               : 5U)
                                           : ((- (IData)(
                                                         (1U 
                                                          & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code)))) 
                                              & (2U 
                                                 | (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)))))))
                                   : Vtop__ConstPool__CONST_hafc400eb_0
                                  [((0x07fffffeU & 
                                     ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code) 
                                      << 1U)) | (0x07ffffffU 
                                                 & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code)))])
                               : ((0xc6b5ffa1U >> ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code) 
                                                   << 2U)) 
                                  & (- (IData)((1U 
                                                & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op))))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__alu_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_ctrl_r;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__alu_ctrl;
}

void Vtop___024root___nba_comb__TOP__4(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_comb__TOP__4\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VdfgRegularize_h6e95ff9d_0_2;
    __VdfgRegularize_h6e95ff9d_0_2 = 0;
    // Body
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__inst_swift)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst_reg
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst);
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func3_code 
        = (7U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                 >> 0x0000000cU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func7_code 
        = (1U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                 >> 0x0000001eU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rd 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 7U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x0000000fU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x00000014U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs1 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x0000000fU));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs2 
        = (0x0000001fU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst 
                          >> 0x00000014U));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op 
        = (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst);
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rd;
    if (VL_UNLIKELY(((0x63U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))))) {
        VL_WRITEF_NX("imm_branch : %d\n",1, '#',32,
                     (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                   >> 0x1fU))) << 0x0000000cU) 
                      | ((0x00000800U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                         << 4U)) | 
                         ((0x000007e0U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                          >> 0x00000014U)) 
                          | (0x0000001eU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                            >> 7U))))));
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__imm_o 
        = (((3U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
            | ((0x13U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
               | (0x67U == (0x0000007fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))))
            ? (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                            >> 0x0000001fU))) << 0x0000000cU) 
               | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                  >> 0x00000014U)) : ((0x23U == (0x0000007fU 
                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))
                                       ? (((- (IData)(
                                                      (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                       >> 0x0000001fU))) 
                                           << 0x0000000cU) 
                                          | ((0x00000fe0U 
                                              & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                 >> 0x00000014U)) 
                                             | (0x0000001fU 
                                                & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                   >> 7U))))
                                       : ((0x63U == 
                                           (0x0000007fU 
                                            & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst))
                                           ? (((- (IData)(
                                                          (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                           >> 0x0000001fU))) 
                                               << 0x0000000cU) 
                                              | ((0x00000800U 
                                                  & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                     << 4U)) 
                                                 | ((0x000007e0U 
                                                     & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                        >> 0x00000014U)) 
                                                    | (0x0000001eU 
                                                       & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                          >> 7U)))))
                                           : (((0x37U 
                                                == 
                                                (0x0000007fU 
                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)) 
                                               | (0x17U 
                                                  == 
                                                  (0x0000007fU 
                                                   & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)))
                                               ? (0xfffff000U 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)
                                               : ((
                                                   ((- (IData)(
                                                               (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                                >> 0x0000001fU))) 
                                                    << 0x00000014U) 
                                                   | ((((0x000001feU 
                                                         & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                            >> 0x0000000bU)) 
                                                        | (1U 
                                                           & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                              >> 0x00000014U))) 
                                                       << 0x0000000bU) 
                                                      | (0x000007feU 
                                                         & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst 
                                                            >> 0x00000014U)))) 
                                                  & (- (IData)(
                                                               (0x6fU 
                                                                == 
                                                                (0x0000007fU 
                                                                 & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst)))))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_read 
        = (3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br_addr_mode 
        = (0x67U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_op 
        = Vtop__ConstPool__TABLE_hf33c53e0_0[vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op];
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write 
        = Vtop__ConstPool__TABLE_h312b9a0c_0[vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op];
    __VdfgRegularize_h6e95ff9d_0_2 = ((0x67U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                                      | (0x6fU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_write 
        = (0x23U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func3_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_func3_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func7_code 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_func7_code;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rd 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rd;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__imm_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_rs2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_read 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_read;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br_addr_mode 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br_addr_mode;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_op 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_op;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__regs_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem2reg 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write) 
           & (3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br 
        = ((0x63U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
           | (IData)(__VdfgRegularize_h6e95ff9d_0_2));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src1 
        = (((0x17U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
            | (IData)(__VdfgRegularize_h6e95ff9d_0_2))
            ? 2U : (1U & (- (IData)((0x37U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op))))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src2 
        = (((3U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
            | ((0x23U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
               | ((0x17U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                  | ((0x37U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op)) 
                     | (0x13U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op))))))
            ? 1U : (2U & (- (IData)((IData)(__VdfgRegularize_h6e95ff9d_0_2)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem2reg 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem2reg;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src1 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src1;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src2;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_imm 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_imm;
    vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write_forward;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_mem_write_forward 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write_forward;
}

void Vtop___024root___nba_comb__TOP__9(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_comb__TOP__9\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_4;
    __VdfgRegularize_h6e95ff9d_0_4 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_5;
    __VdfgRegularize_h6e95ff9d_0_5 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_10;
    __VdfgRegularize_h6e95ff9d_0_10 = 0;
    IData/*31:0*/ __VdfgRegularize_h6e95ff9d_0_11;
    __VdfgRegularize_h6e95ff9d_0_11 = 0;
    // Body
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o
            : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))
                ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data
                : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o
            : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))
                ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data
                : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data1));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B 
        = ((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2))
            ? 4U : ((1U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2))
                     ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm
                     : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_addr_op_A 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br_addr_mode)
            ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc
            : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre);
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A 
        = (((2U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1))
             ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc
             : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre) 
           & (- (IData)((1U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1)))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_pc 
        = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm 
           + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_addr_op_A);
    if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA))))) {
        VL_WRITEF_NX("forwardA! OP_A: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A);
    } else if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB))))) {
        VL_WRITEF_NX("forwardB! OP_B: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B);
    }
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_data2 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_regs_data2_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_pc;
    __VdfgRegularize_h6e95ff9d_0_4 = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                      + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B);
    __VdfgRegularize_h6e95ff9d_0_5 = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                      - vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B);
    __VdfgRegularize_h6e95ff9d_0_10 = (1U & (- (IData)(
                                                       VL_LTS_III(32, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))));
    __VdfgRegularize_h6e95ff9d_0_11 = (1U & (- (IData)(
                                                       (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                                                        < vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o 
        = ((8U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
            ? ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                ? (((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                     ? __VdfgRegularize_h6e95ff9d_0_4
                     : __VdfgRegularize_h6e95ff9d_0_11) 
                   & (- (IData)((1U & (~ ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl) 
                                          >> 1U))))))
                : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_10
                        : __VdfgRegularize_h6e95ff9d_0_5)
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           ^ vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)
                        : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           | vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))))
            : ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)
                        : __VdfgRegularize_h6e95ff9d_0_11)
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_10
                        : VL_SHIFTRS_III(32,32,5, vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A, 
                                         (0x0000001fU 
                                          & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))))
                : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                    ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           >> (0x0000001fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B))
                        : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A 
                           << (0x0000001fU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B)))
                    : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))
                        ? __VdfgRegularize_h6e95ff9d_0_5
                        : __VdfgRegularize_h6e95ff9d_0_4))));
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_addr 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_addr;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__br_mark 
        = ((0x0dU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
           | (((0x0aU == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
               | ((5U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl)) 
                  | (6U == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl))))
               ? (0U != vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o)
               : (0U == vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o)));
    vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_mark 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__br_mark;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_alu_o 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__ex_alu_o;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_ctrl 
        = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br) 
           & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_mark));
    vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_ctrl 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__br_ctrl;
    vlSelfRef.processorci_top__DOT__Processor__DOT__flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
    vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_flush 
        = vlSelfRef.processorci_top__DOT__Processor__DOT__flush;
}

void Vtop___024root___eval_nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__0
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 = 0U;
            if (vlSelfRef.processorci_top__DOT__imem_prog_we) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 
                    = vlSelfRef.processorci_top__DOT__imem_prog_data;
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 
                    = (0x00000fffU & (vlSelfRef.processorci_top__DOT__imem_prog_addr 
                                      >> 2U));
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 = 1U;
            }
        }
    }
    if ((0x000000000000000cULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__1
            IData/*31:0*/ __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
            __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o = 0;
            IData/*31:0*/ __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next;
            __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next = 0;
            __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next;
            __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
            if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn) {
                if ((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_ctrl)))) {
                    if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_stall) {
                        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT____Vstrobe0 = 1U;
                    }
                }
                if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_ctrl))) {
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next 
                        = ((IData)(4U) + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_addr);
                    VL_WRITEF_NX("PC_o = BR_addr: %h\n",1
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o);
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_addr;
                } else if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_stall) {
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next;
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
                    VL_WRITEF_NX("PC_o = stall: %h\n",1
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o);
                } else {
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next 
                        = ((IData)(4U) + vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next);
                    VL_WRITEF_NX("PC_O = PC_next: %h\n",1
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o);
                    __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next;
                }
            } else {
                __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next = 4U;
                __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o = 0U;
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next 
                = __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o 
                = __Vinline_0__nba_sequent__TOP__1___Vdly__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o;
            vlSelfRef.processorci_top__DOT__imem_fetch_addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
            vlSelfRef.processorci_top__DOT__Processor__DOT__if_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc;
            vlSelfRef.imem_fetch_addr = vlSelfRef.processorci_top__DOT__imem_fetch_addr;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr_2 
                = (0x00000fffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr 
                                  >> 2U));
        }
    }
    if ((0x0000000000000041ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__2
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 = 0U;
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 = 0U;
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 = 0U;
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 = 0U;
            vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 = 0U;
        }
    }
    if ((0x0000000000000030ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_sequent__TOP__3(vlSelf);
    }
    if ((0x0000000000006000ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__4
            IData/*31:0*/ __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
            __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc = 0;
            __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
            if (VL_LIKELY(((1U & ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn)) 
                                  | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush)))))) {
                if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush))) {
                    VL_WRITEF_NX("if_id_flush pc: %h\n",1
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc);
                }
                __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc = 0U;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst_reg = 0U;
            } else {
                if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_stall))) {
                    __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
                    VL_WRITEF_NX("if_id_stall, inst: %h, \npc: %h\n",2
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst
                                 , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc);
                } else {
                    __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc 
                        = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_pc;
                }
                VL_WRITEF_NX("id_inst: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst);
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst_reg 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst;
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__inst_swift 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn) 
                   && ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_stall) 
                       | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush)));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc 
                = __Vinline_0__nba_sequent__TOP__4___Vdly__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc;
        }
    }
    if ((0x0000000000000600ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_sequent__TOP__5(vlSelf);
    }
    if ((0x0000000000001800ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_sequent__TOP__6(vlSelf);
    }
    if (VL_UNLIKELY(((0x0000000000000180ULL & vlSelfRef.__VnbaTriggered[0U])))) {
        {
            // Inlined CFunc: _nba_sequent__TOP__7
            VL_WRITEF_NX("wb_alu_o     : %h\nwb_mem2reg   : %h\nwb_regs_write: %h\n-----------------------\n",3
                         , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o
                         , '#',1,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem2reg)
                         , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_regs_write);
            if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_func3_code 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_func3_code;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_rd 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_rd;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_alu_o;
            } else {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_func3_code = 0U;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_rd = 0U;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o = 0U;
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_regs_write 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn) 
                   && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_regs_write));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem2reg 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn) 
                   && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem2reg));
            vlSelfRef.processorci_top__DOT__Processor__DOT__wb_func3_code 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_func3_code;
            vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_rd;
            vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_regs_write;
            vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__wb_alu_o 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_func3_code;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_addr;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_en 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_regs_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_en;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_alu_o;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_addr;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_en;
            vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_regs_write) 
                   & (0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)));
            if (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe0 = 1U;
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe1 = 1U;
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb 
                = (3U & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o);
            vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en) 
                   & (0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)));
        }
    }
    if ((0x0000000000018000ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__8
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr2 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn) 
                   && (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr1));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__syn_rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr2;
            vlSelfRef.processorci_top__DOT__Processor__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__syn_rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn;
        }
    }
    if (VL_UNLIKELY(((0x0000000000000040ULL & vlSelfRef.__VnbaTriggered[0U])))) {
        {
            // Inlined CFunc: _nba_sequent__TOP__9
            if (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs) 
                 & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we))) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 
                    = (0x000000ffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata);
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr;
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 = 1U;
            }
            if (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs) 
                 & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we) 
                    >> 1U))) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 
                    = (0x000000ffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata 
                                      >> 8U));
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr;
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 = 1U;
            }
            if (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs) 
                 & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we) 
                    >> 2U))) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 
                    = (0x000000ffU & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata 
                                      >> 0x10U));
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr;
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 = 1U;
            }
            if (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs) 
                 & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we) 
                    >> 3U))) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 
                    = (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata 
                       >> 0x18U);
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 
                    = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr;
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 = 1U;
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__rdata 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs) 
                    & (~ (0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we))))
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem
                   [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr]
                    : 0U);
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__r_data_mem 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__rdata;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__r_data_mem 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__r_data_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__r_data_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem_data;
            VL_WRITEF_NX("wb_mem_data  : %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data);
            vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__wb_mem_data;
        }
    }
    if ((2ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__10
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__rdata 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__cs)
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem
                   [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__addr]
                    : 0U);
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_o 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__rdata;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_inst 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_o;
            vlSelfRef.processorci_top__DOT__Processor__DOT__if_inst 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_inst;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__if_inst;
        }
    }
    if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__11
            if (vlSelfRef.processorci_top__DOT__dmem_prog_we) {
                vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 
                    = vlSelfRef.processorci_top__DOT__dmem_prog_data;
                vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 
                    = (0x00000fffU & (vlSelfRef.processorci_top__DOT__dmem_prog_addr 
                                      >> 2U));
                vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 = 1U;
            }
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0] 
                    = vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0;
            }
        }
    }
    if ((0x000000000000000cULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__12
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__if_pc;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr_2;
        }
    }
    if ((0x0000000000006000ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__13
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_pc 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_pc;
        }
    }
    if ((0x0000000000001e00ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__0
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_6));
        }
    }
    if ((0x0000000000000600ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__14
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_func3_code 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_func3_code;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_rd 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_rd;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_regs_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_regs_write;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_alu_o 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__me_alu_o;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__en_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_en_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem_2;
        }
    }
    if ((0x0000000000000780ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__1
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_mem2reg) 
                   & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_mem_write) 
                      & ((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
                         & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd) 
                            == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rs2)))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__forward_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__forward_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__forward_data;
        }
    }
    if ((0x0000000000001980ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__2
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_7));
        }
    }
    if ((0x00000000000001c0ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__3
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o 
                = ((4U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                    ? (0x0000ffffU & ((- (IData)((1U 
                                                  & (~ 
                                                     ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code) 
                                                      >> 1U))))) 
                                      & ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                                          ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                              ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                 >> 0x00000010U)
                                              : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)
                                          : (0x000000ffU 
                                             & ((2U 
                                                 & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                                 ? 
                                                ((1U 
                                                  & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                                  ? 
                                                 (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 0x00000018U)
                                                  : 
                                                 (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 0x00000010U))
                                                 : 
                                                ((1U 
                                                  & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                                  ? 
                                                 (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 8U)
                                                  : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data))))))
                    : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                        ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                           & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))))))
                        : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code))
                            ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                ? (((- (IData)((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                >> 0x0000001fU))) 
                                    << 0x00000010U) 
                                   | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                      >> 0x00000010U))
                                : (((- (IData)((1U 
                                                & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                   >> 0x0000000fU)))) 
                                    << 0x00000010U) 
                                   | (0x0000ffffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)))
                            : ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                ? ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                    ? (((- (IData)(
                                                   (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                    >> 0x0000001fU))) 
                                        << 8U) | (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                  >> 0x00000018U))
                                    : (((- (IData)(
                                                   (1U 
                                                    & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                       >> 0x00000017U)))) 
                                        << 8U) | (0x000000ffU 
                                                  & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                     >> 0x00000010U))))
                                : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb))
                                    ? (((- (IData)(
                                                   (1U 
                                                    & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                       >> 0x0000000fU)))) 
                                        << 8U) | (0x000000ffU 
                                                  & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                     >> 8U)))
                                    : (((- (IData)(
                                                   (1U 
                                                    & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data 
                                                       >> 7U)))) 
                                        << 8U) | (0x000000ffU 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data)))))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg)
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o
                    : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o);
            vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_regs_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__w_regs_data;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_data;
        }
    }
    if ((0x0000000000006002ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_comb__TOP__4(vlSelf);
    }
    if ((0x0000000000000041ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_sequent__TOP__15
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0] 
                    = vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0;
            }
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1] 
                    = ((0xffffff00U & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem
                        [vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1]) 
                       | (IData)(vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1));
            }
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2] 
                    = ((0xffff00ffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem
                        [vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2]) 
                       | ((IData)(vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2) 
                          << 8U));
            }
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3] 
                    = ((0xff00ffffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem
                        [vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3]) 
                       | ((IData)(vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3) 
                          << 0x00000010U));
            }
            if (vlSelfRef.__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4) {
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4] 
                    = ((0x00ffffffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem
                        [vlSelfRef.__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4]) 
                       | ((IData)(vlSelfRef.__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4) 
                          << 0x00000018U));
            }
        }
    }
    if ((0x0000000000001f80ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__5
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b)
                    ? 2U : (1U & (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b)))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a)
                    ? 2U : (1U & (- (IData)((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a)))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__forwardB 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB;
            if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA))))) {
                VL_WRITEF_NX("forwardA! ex_hazard: %b, mem_hazard: %b\n",2
                             , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a
                             , '#',1,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a));
            } else if (VL_UNLIKELY(((0U != (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB))))) {
                VL_WRITEF_NX("forwardB! ex_hazard: %b, mem_hazard: %b\n",2
                             , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b
                             , '#',1,(IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b));
            } else if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data))) {
                VL_WRITEF_NX("forward4store! hazard_data: %b\n",1
                             , '#',1,vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem);
            }
            vlSelfRef.processorci_top__DOT__Processor__DOT__forwardA 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__forwardB;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__forwardA;
        }
    }
    if ((0x00000000000007c0ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__6
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__forward_data)
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_regs_data
                    : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_regs_data2);
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem 
                = ((0U == (3U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code)))
                    ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                        ? (((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                             ? (0x0000ff00U & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                                               << 8U))
                             : (0x000000ffU & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre)) 
                           << 0x00000010U) : ((1U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                                               ? (0x0000ff00U 
                                                  & (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                                                     << 8U))
                                               : (0x000000ffU 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre)))
                    : ((1U == (3U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code)))
                        ? ((2U & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word))
                            ? (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                               << 0x00000010U) : (0x0000ffffU 
                                                  & vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre))
                        : (vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre 
                           & (- (IData)((2U == (3U 
                                                & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code))))))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_data_mem 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem;
            vlSelfRef.processorci_top__DOT__adam_mem_wdata 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_data_mem;
            vlSelfRef.processorci_top__DOT__core_data_out 
                = vlSelfRef.processorci_top__DOT__adam_mem_wdata;
            vlSelfRef.processorci_top__DOT__data_mem_data_out 
                = vlSelfRef.processorci_top__DOT__adam_mem_wdata;
            vlSelfRef.core_data_out = vlSelfRef.processorci_top__DOT__core_data_out;
            vlSelfRef.data_mem_data_out = vlSelfRef.processorci_top__DOT__data_mem_data_out;
        }
    }
    if ((0x0000000000006182ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__7
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_a 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_b 
                = (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2) 
                    == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr)) 
                   & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3));
        }
    }
    if ((0x0000000000007802ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__8
            vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs2) 
                   == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__load_stall 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read) 
                   & ((IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8) 
                      | ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs1) 
                         == (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__stall 
                = ((~ ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read) 
                       & ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_mem_write_forward) 
                          & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_8)))) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__load_stall));
            vlSelfRef.processorci_top__DOT__Processor__DOT__stall 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__stall;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_stall 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__pc_stall 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_stall 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__stall;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_stall 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__pc_stall;
        }
    }
    if ((0x0000000000001fc0ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_comb__TOP__9(vlSelf);
    }
    if ((0x00000000000061f2ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__10
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o1 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_a)
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data
                    : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank
                   [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1]);
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o2 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_b)
                    ? vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data
                    : vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank
                   [vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2]);
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o1;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data2 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o2;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data1;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data2 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data2;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data1;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data2 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_data2;
        }
    }
    if ((0x000000000001f802ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__11
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve 
                = (1U & ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn)) 
                         | (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_stall)));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_read 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_read));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem2reg 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem2reg));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_op 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_op) 
                   & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src1 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src1) 
                   & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src2 
                = ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src2) 
                   & (- (IData)((1U & (~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve))))));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br_addr_mode 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br_addr_mode));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_write 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__regs_write));
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_br 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_read 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_read;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_op 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_op;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src1;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src2 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src2;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_br_addr_mode 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br_addr_mode;
            vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_write;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_br;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_read 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_read;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem2reg 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem2reg;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_op 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_op;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_mem_write;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src1 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src1;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src2 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_alu_src2;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br_addr_mode 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_br_addr_mode;
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_write 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__id_regs_write;
        }
    }
    if ((0x0000000000019fc0ULL & vlSelfRef.__VnbaTriggered[0U])) {
        {
            // Inlined CFunc: _nba_comb__TOP__12
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__rstn 
                = ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_flush)) 
                   & (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn));
            vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__cs 
                = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__rstn;
        }
    }
}

void Vtop___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtop___024root___eval_phase__act(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__act\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__act
        vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                        ((((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn)) 
                                                           & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn__0)) 
                                                          << 0x00000010U) 
                                                         | ((((((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock) 
                                                                  & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock__0))) 
                                                                 << 3U) 
                                                                | (((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn)) 
                                                                    & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn__0)) 
                                                                   << 2U)) 
                                                               | ((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk) 
                                                                    & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk__0))) 
                                                                   << 1U) 
                                                                  | ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn)) 
                                                                     & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn__0)))) 
                                                              << 0x0000000cU) 
                                                             | ((((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk) 
                                                                    & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk__0))) 
                                                                   << 3U) 
                                                                  | (((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn)) 
                                                                      & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn__0)) 
                                                                     << 2U)) 
                                                                 | ((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk) 
                                                                      & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk__0))) 
                                                                     << 1U) 
                                                                    | ((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn)) 
                                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn__0)))) 
                                                                << 8U)) 
                                                            | (((((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk) 
                                                                    & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk__0))) 
                                                                   << 3U) 
                                                                  | (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk) 
                                                                      & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk__0))) 
                                                                     << 2U)) 
                                                                 | ((((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn)) 
                                                                      & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn__0)) 
                                                                     << 1U) 
                                                                    | ((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk) 
                                                                       & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk__0))))) 
                                                                << 4U) 
                                                               | (((((~ (IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn)) 
                                                                     & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn__0)) 
                                                                    << 3U) 
                                                                   | (((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk) 
                                                                       & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk__0))) 
                                                                      << 2U)) 
                                                                  | ((((IData)(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk) 
                                                                       & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk__0))) 
                                                                      << 1U) 
                                                                     | ((IData)(vlSelfRef.processorci_top__DOT__clk_core) 
                                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__clk_core__0))))))))));
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__clk_core__0 
            = vlSelfRef.processorci_top__DOT__clk_core;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock;
        vlSelfRef.__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn__0 
            = vlSelfRef.processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn;
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vtop___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vtop___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtop___024root___eval_phase__nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vtop___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vtop___024root___eval_nba(vlSelf);
        Vtop___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vtop___024root___eval(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/home/gabcro/Code/Processor_CI/RV-Bench/wrappers_golden/AdamRiscv.sv", 15, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 10000 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = Vtop___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/gabcro/Code/Processor_CI/RV-Bench/wrappers_golden/AdamRiscv.sv", 15, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/gabcro/Code/Processor_CI/RV-Bench/wrappers_golden/AdamRiscv.sv", 15, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vtop___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vtop___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
    {
        // Inlined CFunc: _eval_postponed
        {
            // Inlined CFunc: _eval_postponed__TOP
            if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT____Vstrobe0))) {
                VL_WRITEF_NX("PC_next = stall: %h\n",1
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next);
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT____Vstrobe0 = 0U;
            }
            if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT____Vstrobe0))) {
                VL_WRITEF_NX("WRITE DATA MEMORY: Addr %d = %h \n",2
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem);
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT____Vstrobe0 = 0U;
            }
            if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe0))) {
                VL_WRITEF_NX("WHOLE-WORD READ FROM DATA MEMORY : Addr %d = %h \n",2
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data);
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe0 = 0U;
            }
            if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe1))) {
                VL_WRITEF_NX("DATA IN LOAD-INST : %d\n",1
                             , '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o);
                vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe1 = 0U;
            }
        }
    }
}

#ifdef VL_DEBUG
void Vtop___024root___eval_debug_assertions(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_debug_assertions\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.sys_clk & 0xfeU)))) {
        Verilated::overWidthError("sys_clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst_n & 0xfeU)))) {
        Verilated::overWidthError("rst_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.imem_prog_we & 0xfeU)))) {
        Verilated::overWidthError("imem_prog_we");
    }
    if (VL_UNLIKELY(((vlSelfRef.dmem_prog_we & 0xfeU)))) {
        Verilated::overWidthError("dmem_prog_we");
    }
    if (VL_UNLIKELY(((vlSelfRef.core_ack & 0xfeU)))) {
        Verilated::overWidthError("core_ack");
    }
    if (VL_UNLIKELY(((vlSelfRef.data_mem_ack & 0xfeU)))) {
        Verilated::overWidthError("data_mem_ack");
    }
}
#endif  // VL_DEBUG
