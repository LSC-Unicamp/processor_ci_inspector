// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

VL_ATTR_COLD void Vtop___024root___eval_static(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_static\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
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

VL_ATTR_COLD void Vtop___024root___eval_initial(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_initial__TOP
        IData/*31:0*/ __Vinline_0__eval_initial__TOP_processorci_top__DOT____VlemExpr_0;
        __Vinline_0__eval_initial__TOP_processorci_top__DOT____VlemExpr_0 
            = VL_VALUEPLUSARGS_INN(64, "MEMORY_HEX=%s"s, 
                                   vlSelfRef.processorci_top__DOT__memory_hex_file);
        if ((! __Vinline_0__eval_initial__TOP_processorci_top__DOT____VlemExpr_0)) {
            vlSelfRef.processorci_top__DOT__memory_hex_file = "/home/gabcro/Code/Processor_CI/processor_ci_wrapper/internal/memory.hex"s;
        }
        VL_READMEM_N(true, 32, 4096, 0, vlSelfRef.processorci_top__DOT__memory_hex_file
                     ,  &(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem)
                     , 0, ~0ULL);
        VL_READMEM_N(true, 32, 4096, 0, vlSelfRef.processorci_top__DOT__memory_hex_file
                     ,  &(vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem)
                     , 0, ~0ULL);
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__we = 0U;
        vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__wdata = 0U;
    }
}

VL_ATTR_COLD void Vtop___024root___eval_final(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_final\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_settle(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_settle\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/gabcro/Code/Processor_CI/RV-Bench/wrappers_golden/AdamRiscv.sv", 15, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vtop___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD bool Vtop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vtop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vtop___024root___stl_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___stl_sequent__TOP__0\n"); );
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

VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__stl\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__stl
        vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                          & vlSelfRef.__VstlTriggered[0U]) 
                                         | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vtop___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        {
            // Inlined CFunc: _eval_stl
            if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
                Vtop___024root___stl_sequent__TOP__0(vlSelf);
            }
        }
    }
    return (__VstlExecute);
}

bool Vtop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vtop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge processorci_top.clk_core)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge processorci_top.Processor.u_stage_if.u_inst_memory.u_ram_data.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(posedge processorci_top.Processor.u_stage_if.u_pc.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 3U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 3 is active: @(negedge processorci_top.Processor.u_stage_if.u_pc.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 4U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 4 is active: @(posedge processorci_top.Processor.u_stage_id.u_regs.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 5U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 5 is active: @(negedge processorci_top.Processor.u_stage_id.u_regs.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 6U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 6 is active: @(posedge processorci_top.Processor.u_stage_mem.u_data_memory.u_ram_data.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 7U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 7 is active: @(posedge processorci_top.Processor.u_reg_mem_wb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 8U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 8 is active: @(negedge processorci_top.Processor.u_reg_mem_wb.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 9U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 9 is active: @(posedge processorci_top.Processor.u_reg_ex_mem.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000aU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 10 is active: @(negedge processorci_top.Processor.u_reg_ex_mem.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000bU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 11 is active: @(posedge processorci_top.Processor.u_reg_id_ex.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000cU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 12 is active: @(negedge processorci_top.Processor.u_reg_id_ex.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000dU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 13 is active: @(posedge processorci_top.Processor.u_reg_if_id.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000eU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 14 is active: @(negedge processorci_top.Processor.u_reg_if_id.rstn)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000fU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 15 is active: @(posedge processorci_top.Processor.u_syn_rst.clock)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x00000010U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 16 is active: @(negedge processorci_top.Processor.u_syn_rst.rstn)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtop___024root___eval_postponed(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_postponed\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_postponed__TOP
        if (VL_UNLIKELY((vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT____Vstrobe0))) {
            VL_WRITEF_NX("PC_next = stall: %h\n",1, '#',32,vlSelfRef.processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next);
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

VL_ATTR_COLD void Vtop___024root___ctor_var_reset(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ctor_var_reset\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->sys_clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7302336598091101382ull);
    vlSelf->rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1638864771569018232ull);
    vlSelf->core_cyc = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1141577675992920579ull);
    vlSelf->core_stb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11536184275835517213ull);
    vlSelf->core_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6110123358696410442ull);
    vlSelf->core_sel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12275522221798897536ull);
    vlSelf->core_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10055046685061401977ull);
    vlSelf->core_data_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13636778918381906204ull);
    vlSelf->core_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3846494081212098640ull);
    vlSelf->imem_prog_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8198465803067125669ull);
    vlSelf->imem_prog_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2990632118750888001ull);
    vlSelf->imem_prog_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11606262770104085580ull);
    vlSelf->dmem_prog_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10846809410354574750ull);
    vlSelf->dmem_prog_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15152546758919603725ull);
    vlSelf->dmem_prog_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7356491761527458482ull);
    vlSelf->imem_fetch_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15376435277647897437ull);
    vlSelf->core_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17615053810593628266ull);
    vlSelf->data_mem_cyc = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5343550444735118436ull);
    vlSelf->data_mem_stb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17272977853798743515ull);
    vlSelf->data_mem_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 415970957181446690ull);
    vlSelf->data_mem_sel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 13783874420385300638ull);
    vlSelf->data_mem_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13246612461808756485ull);
    vlSelf->data_mem_data_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14558979008259780061ull);
    vlSelf->data_mem_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5858601597125303240ull);
    vlSelf->data_mem_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17794832759161164577ull);
    vlSelf->processorci_top__DOT__sys_clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 634991966594989971ull);
    vlSelf->processorci_top__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3319644405266965904ull);
    vlSelf->processorci_top__DOT__core_cyc = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16235628547817186015ull);
    vlSelf->processorci_top__DOT__core_stb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5076991245120864195ull);
    vlSelf->processorci_top__DOT__core_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6857689236826378542ull);
    vlSelf->processorci_top__DOT__core_sel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 18030967141402536781ull);
    vlSelf->processorci_top__DOT__core_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5258969079752646303ull);
    vlSelf->processorci_top__DOT__core_data_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9255495554212958074ull);
    vlSelf->processorci_top__DOT__core_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18037064148725606455ull);
    vlSelf->processorci_top__DOT__imem_prog_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13549700127007684086ull);
    vlSelf->processorci_top__DOT__imem_prog_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18334407672122330374ull);
    vlSelf->processorci_top__DOT__imem_prog_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5549840369526711684ull);
    vlSelf->processorci_top__DOT__dmem_prog_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1376623886783620364ull);
    vlSelf->processorci_top__DOT__dmem_prog_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6351891402074011590ull);
    vlSelf->processorci_top__DOT__dmem_prog_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3821411803763362969ull);
    vlSelf->processorci_top__DOT__imem_fetch_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6807291548196483279ull);
    vlSelf->processorci_top__DOT__core_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11921823956539627932ull);
    vlSelf->processorci_top__DOT__data_mem_cyc = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11903641629270274300ull);
    vlSelf->processorci_top__DOT__data_mem_stb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9282946035449225936ull);
    vlSelf->processorci_top__DOT__data_mem_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16357415441953824577ull);
    vlSelf->processorci_top__DOT__data_mem_sel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6728749866102666070ull);
    vlSelf->processorci_top__DOT__data_mem_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1640989804271727232ull);
    vlSelf->processorci_top__DOT__data_mem_data_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 892440154701597481ull);
    vlSelf->processorci_top__DOT__data_mem_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15579686411038238752ull);
    vlSelf->processorci_top__DOT__data_mem_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3844350989934196969ull);
    vlSelf->processorci_top__DOT__clk_core = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14524758976223310908ull);
    vlSelf->processorci_top__DOT__rst_core = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15174876808446487310ull);
    vlSelf->processorci_top__DOT___core_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16125324822266323414ull);
    vlSelf->processorci_top__DOT___core_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3063875534087011067ull);
    vlSelf->processorci_top__DOT___data_mem_data_in = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8855725038720641034ull);
    vlSelf->processorci_top__DOT___data_mem_ack = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13408481674898787066ull);
    vlSelf->processorci_top__DOT__adam_mem_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6381328581935381013ull);
    vlSelf->processorci_top__DOT__adam_mem_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8351017636039409064ull);
    vlSelf->processorci_top__DOT__adam_mem_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7832575673843803186ull);
    vlSelf->processorci_top__DOT__adam_mem_wdata = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11790234491750195944ull);
    vlSelf->processorci_top__DOT__adam_mem_wstrb = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 2291477075683541862ull);
    vlSelf->processorci_top__DOT__adam_bus_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14422501372799762820ull);
    vlSelf->processorci_top__DOT__Processor__DOT__sys_clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5123432746605526511ull);
    vlSelf->processorci_top__DOT__Processor__DOT__sys_rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13720945362655120969ull);
    vlSelf->processorci_top__DOT__Processor__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14447508373577906648ull);
    vlSelf->processorci_top__DOT__Processor__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5823548257689576280ull);
    vlSelf->processorci_top__DOT__Processor__DOT__br_ctrl = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2724239124165230078ull);
    vlSelf->processorci_top__DOT__Processor__DOT__br_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6216703799758516672ull);
    vlSelf->processorci_top__DOT__Processor__DOT__stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17599245546549204477ull);
    vlSelf->processorci_top__DOT__Processor__DOT__if_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15456307785602059924ull);
    vlSelf->processorci_top__DOT__Processor__DOT__if_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3685788996231468393ull);
    vlSelf->processorci_top__DOT__Processor__DOT__flush = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1972980308419140388ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11909670575909687926ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2445527660706255387ull);
    vlSelf->processorci_top__DOT__Processor__DOT__w_regs_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6247743403949111635ull);
    vlSelf->processorci_top__DOT__Processor__DOT__w_regs_addr = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 16156011484740263071ull);
    vlSelf->processorci_top__DOT__Processor__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6902083545138083550ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5920511408009979382ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15022284362954347708ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4958092850358452649ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 15491246213092355986ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14417178905070147193ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 3582615123524866106ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11915213973663783894ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 22489562166556472ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15933371332394688655ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 1368882761447779324ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10337239709072224330ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 15830879170330290042ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 6507062367602011832ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15495305041777398985ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5509071391840564560ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_mem_write_forward = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12977965695833409659ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 17494681486641749450ull);
    vlSelf->processorci_top__DOT__Processor__DOT__id_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 13749292585952687329ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 11212419530006749463ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 4814336892024768981ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2611118147459752464ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5776080260700209285ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12926395460214161593ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7416767138020409670ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 9808672408206516364ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6041414280255478391ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8267319712547304347ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6575611232816159644ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10450463616299396204ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1091836824465253978ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 16137474879769468329ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2168551994428839411ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2754095989203396523ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2064859225627006633ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7367129486933976373ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6189411694635526102ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_regs_data2_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15578925781724169459ull);
    vlSelf->processorci_top__DOT__Processor__DOT__ex_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16641403570910725054ull);
    vlSelf->processorci_top__DOT__Processor__DOT__forwardA = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 8567544105476602740ull);
    vlSelf->processorci_top__DOT__Processor__DOT__forwardB = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2930933799817633508ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8733419945586348375ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14112250630851724960ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8538407649909113081ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 2066130664044481613ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10644874089711024072ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4043951173142370192ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6534863179708535269ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6010722710300613425ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15713622108371210624ull);
    vlSelf->processorci_top__DOT__Processor__DOT__me_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 8407299846789809837ull);
    vlSelf->processorci_top__DOT__Processor__DOT__forward_data = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 890695446016107599ull);
    vlSelf->processorci_top__DOT__Processor__DOT__wb_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 6228046457416672412ull);
    vlSelf->processorci_top__DOT__Processor__DOT__wb_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 813286475123447749ull);
    vlSelf->processorci_top__DOT__Processor__DOT__wb_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17184812718123969305ull);
    vlSelf->processorci_top__DOT__Processor__DOT__wb_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4710734519571555954ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4589814079664062920ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7890958313882970994ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__pc_stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14245018840319461971ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_flush = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15358139798515604548ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9191027515902691439ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__br_ctrl = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11186154444985116396ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16908541216503714626ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__if_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2030835950563043197ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13214977868966878312ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3778517563284156433ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16212330335976492394ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 104788904021470596ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__inst_addr_2 = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 10367814082180237823ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16252399164916968995ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__cs = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1911184102015218641ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__we = 0U;
    ;
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__addr = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 4659444507421704895ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__wdata = 0U;
    ;
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__rdata = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13645306146656702429ull);
    for (int __Vi0 = 0; __Vi0 < 4096; ++__Vi0) {
        vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12364285132538415485ull);
    }
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18231703236599286766ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_ctrl = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14568504239253809348ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__br_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10183175308835918329ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11385633032599751794ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9890951063430090537ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11293728943915721566ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__pc_next = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9656342176679886315ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT____Vstrobe0 = 0;
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3141376729956786123ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1894129624593465950ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6766587677310331788ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12758347190874078824ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_addr = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 10383274593515628699ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14100931399324557888ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12122003953071454255ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2139170664664784263ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4299571984104028651ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14465250445201718676ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 7523579809825293931ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2031462836620147562ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 10670443163744761548ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7529802299700827686ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18171294424636413182ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15390271139897007759ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 2633946181242126058ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16216009745478254206ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1952129144849608796ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 10451189180713670364ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 252429399405982794ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13172404385472700497ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_mem_write_forward = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10382552248894728137ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 17948351227596143209ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__id_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 10555472916002701749ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8799924278711111204ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10907599531614048250ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14160558813793605852ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 8570950266643136101ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17520424271261768489ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 7674670204685920987ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 725747537928273920ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3272442629167744537ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2215977849783201233ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__ctrl_valve = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14768170215000661598ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2228504315597607728ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_imm_gen__DOT__imm_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5118297854305023122ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__inst_op = VL_SCOPED_RAND_RESET_I(7, __VscopeHash, 4893113429131925659ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11982561359349910425ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8799542709168129694ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3166278081412034949ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 8446508274560206842ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11893836458824898955ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 8557655787385915361ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2302894602725596544ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14978180788962669171ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_ctrl__DOT__regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6906756211039461571ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2053087217322596516ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14270083294371816831ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 15650219617196526355ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_addr2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 10923292903848449284ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_addr = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 127353923244292724ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16869604588566310858ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__w_regs_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13130756129618158588ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7098928710334988491ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__r_regs_o2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14901625770201366162ull);
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__reg_bank[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8712363779971647136ull);
    }
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_a = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16822873602481295236ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__wb_hazard_b = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6952677735855778282ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10911060838025522935ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 369488858761641377ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9478621452209442330ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2468813245588202236ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16573413773625855570ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11534052711490732494ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3914039048512162858ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__forward_data = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11303593391823338064ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7646933096015900679ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__me_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6176761812274511015ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16406441475791630464ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_data_mem_pre = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17896373371122661309ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__r_data_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4445456024500980495ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__w_en_mem = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 8205608967166762162ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7749329881605265226ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__addr_in_word = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 7812611859595135494ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__en_mem = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13203232028631558343ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT____Vstrobe0 = 0;
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 509999284181187391ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7166532648599556607ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_data_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15156097478982659662ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__w_en_mem = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 11359165046601158949ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__en_mem = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12778629434494181186ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__r_data_mem = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11887834912228872540ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__addr_mem_2 = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 17449348878314507169ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16737222359371403999ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__cs = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17271370096463142568ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__we = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 7266509736773831096ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__addr = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 12300441165945436066ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__wdata = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17683001764934410339ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__rdata = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12644988450250615557ull);
    for (int __Vi0 = 0; __Vi0 < 4096; ++__Vi0) {
        vlSelf->processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 324774924686344908ull);
    }
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9400106890947388869ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 675339669799413599ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8009732072212869644ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13889307711716994143ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 7715122394769403308ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11365639328880736967ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 5462584659201733405ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 11921006782330731149ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1328353493234139336ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5015091708248047376ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1046429536532499122ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardA = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 3977201806520443905ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__forwardB = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 11617317340785357499ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__me_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8656190703113199779ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3411944341921778004ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10913919655382933439ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__ex_regs_data2_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15300833092863856499ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8223538037437544983ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_ctrl = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5752653250486466010ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__alu_ctrl = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 7985223279873572409ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15975548019926958042ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_A_pre = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9431791382433761676ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15998490031415665757ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__op_B_pre = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18179818075917892140ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_mark = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8292577091525336544ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__br_addr_op_A = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2829432727920213454ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_ctrl = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 11421146041217590198ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_A = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13199593325291677123ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__op_B = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7265028916216392016ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4980140126163406552ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu__DOT__br_mark = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8344358495862712709ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 6111414468496414192ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3581907003770883644ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13032904198105176870ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_ex__DOT__u_alu_control__DOT__alu_ctrl_r = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12149870258821939144ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2068678104447883427ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 5528229450244143560ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 14125726665140651007ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__ex_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8719391627954908677ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__br_ctrl = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11361907103666991769ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__id_mem_write_forward = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5444640697481688146ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1347285712361315486ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__flush = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9386998178510582119ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_hazard_detection__DOT__load_stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13095743885815721731ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 14031807695947092580ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 12254961327517741353ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 4650726017715083275ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 6291875605318305775ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 11180200554024336504ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5910643896913895191ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4002270681278693454ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__me_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10749511878803499896ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__wb_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8875391607549954708ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardA = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 4290110709518889076ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forwardB = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 14410528366093783865ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__forward_data = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15105277446220852307ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_a = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15735625753679987676ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__ex_hazard_b = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9583609549779471209ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_a = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17914153242764784037ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__mem_hazard_b = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11951029855786812507ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_forwarding__DOT__hazard_data_mem = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12982187317640688546ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10805770867020240474ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6802709111027242639ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17560657367093296805ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 15799026186231875788ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__w_regs_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17188724319357844661ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__wb_mem_data_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6124112017426971708ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT__addr_in_word_wb = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 8273894348223232859ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe0 = 0;
    vlSelf->processorci_top__DOT__Processor__DOT__u_stage_wb__DOT____Vstrobe1 = 0;
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15855015817565921005ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15148997437396265694ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13896586927335091238ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8346611414748382453ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 5360793140321668879ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2412637681965621130ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1376361414270838908ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__me_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 739499143348053038ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 2826755185599810180ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem_data = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11160131018563126230ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17667215394610963433ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 18103117111320564543ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 95438587791690974ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__wb_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8634423669984573472ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13968723801076765471ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6271450427075576310ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14274401036174718321ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3118483938045141229ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8172639737916564816ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17712002564490374875ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8781466514321073662ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9316434210927591552ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17801113468647742980ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17703625526969170646ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__ex_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8062439031774699469ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 9536740008489526975ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6184802523561389657ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_alu_o = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14761558304867693938ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 9572880780454042476ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13466665831620381071ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9916364151466262634ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10810557266546745108ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2179186166958107763ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__me_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 705532081158110956ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16399597382128752807ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10136298281647954244ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10690316886332153539ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15207914558710584358ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3293012418580625177ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15166904099634080615ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 13052650553970035201ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3105714238732028172ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 7963952603990202044ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11131642637997977830ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10466626691237293241ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12188779574896690122ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 11234321560466016560ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9129777935778710996ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2039876843177767099ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 10880974435030942747ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12505879329311920784ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16479260249965999049ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_ex_flush = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3834370417995323128ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 12980842868684692785ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__id_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 12322980065600265414ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs1 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 13073592208277580787ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rs2 = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 9808273299043636698ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13327028474860019240ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12204426756186580546ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_data2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15359093041454030625ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_imm = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5865158276722297360ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func3_code = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17710874248519207966ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_func7_code = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1559920361472349989ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 4240128670439517505ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15260817902196514188ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_read = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10251028799838824948ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem2reg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9034387868370239085ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_op = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12579016758490857285ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_mem_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10017852986292603611ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 5450789111953647928ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_alu_src2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 12185084734440545945ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_br_addr_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12408373076899842622ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__ex_regs_write = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1661580226490032465ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12311193569455125358ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13631209597135453699ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18092325535545542582ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13183650258372264091ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15392495322588346571ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8234278018302744483ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_flush = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10724830074876447791ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__if_id_stall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6924884247698992811ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__id_inst_reg = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3233586345569756350ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__inst_swift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16642113066800812681ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12164275238629076385ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6462887824386394885ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__syn_rstn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6052213570739196558ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr1 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17652028144035862146ull);
    vlSelf->processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rst_nr2 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10865777018382118306ull);
    vlSelf->__VdfgRegularize_h6e95ff9d_0_3 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_6 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_7 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_8 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v0 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v1 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v2 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v3 = 0;
    vlSelf->__VdlyVal__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 = 0;
    vlSelf->__VdlyDim0__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 = 0;
    vlSelf->__VdlySet__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__mem__v4 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__clk_core__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_pc__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_id__DOT__u_regs__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_mem_wb__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_ex_mem__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_id_ex__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_reg_if_id__DOT__rstn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__clock__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__processorci_top__DOT__Processor__DOT__u_syn_rst__DOT__rstn__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
