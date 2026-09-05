// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VTOP__SYMS_H_
#define VERILATED_VTOP__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vtop.h"

// INCLUDE MODULE CLASSES
#include "Vtop___024root.h"

// DPI TYPES for DPI Export callbacks (Internal use)

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vtop__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vtop* const __Vm_modelp;
    bool __Vm_activity = false;  ///< Used by trace routines to determine change occurred
    uint32_t __Vm_baseCode = 0;  ///< Used by trace routines when tracing multiple models
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vtop___024root                 TOP;

    // SCOPE NAMES
    VerilatedScope* __Vscopep_TOP;
    VerilatedScope* __Vscopep_processorci_top;
    VerilatedScope* __Vscopep_processorci_top__Processor;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_forwarding;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_hazard_detection;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_reg_ex_mem;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_reg_id_ex;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_reg_if_id;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_reg_mem_wb;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_ex;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_ex__u_alu;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_ex__u_alu_control;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_id;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_id__u_ctrl;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_id__u_imm_gen;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_id__u_regs;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_if;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_if__u_inst_memory;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_if__u_inst_memory__u_ram_data;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_if__u_pc;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_mem;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_mem__u_data_memory;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_mem__u_data_memory__u_ram_data;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_stage_wb;
    VerilatedScope* __Vscopep_processorci_top__Processor__u_syn_rst;

    // SCOPE HIERARCHY
    VerilatedHierarchy __Vhier;

    // CONSTRUCTORS
    Vtop__Syms(VerilatedContext* contextp, const char* namep, Vtop* modelp);
    ~Vtop__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
