// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

// Parameter definitions for Vtop___024root
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__IROM_SPACE;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__ADDR_WIDTH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__DATA_WHITH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__DATA_SIZE;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__ADDR_WHITH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__RAM_DEPTH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_if__DOT__u_inst_memory__DOT__u_ram_data__DOT__DATA_BYTE;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__RAM_SPACE;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__ADDR_WIDTH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__DATA_WHITH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__DATA_SIZE;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__ADDR_WHITH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__RAM_DEPTH;
constexpr IData/*31:0*/ Vtop___024root::processorci_top__DOT__Processor__DOT__u_stage_mem__DOT__u_data_memory__DOT__u_ram_data__DOT__DATA_BYTE;


void Vtop___024root___ctor_var_reset(Vtop___024root* vlSelf);

Vtop___024root::Vtop___024root(Vtop__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vtop___024root___ctor_var_reset(this);
}

void Vtop___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vtop___024root::~Vtop___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
