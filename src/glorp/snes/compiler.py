from .ram import SnesRAM
from .rom import SnesROM
from ..lexparse.ast import AST

from enum import Enum

class SnesAddressMode(Enum):
    ABSOLUTE  = "absolute"
    ABSOLUTE_INDEXED_BY_X = "absolute indexed by x"
    ABSOLUTE_INDEXED_BY_Y = "absolute indexed by y"
    ABSOLUTE_LONG = "absolute_long"
    ABSOLUTE_LONG_INDEXED_BY_X = "absolute long indexed by x"
    DIRECT_PAGE = "direct page"
    DIRECT_PAGE_INDEXED_BY_X = "direct page indexed by x"
    DIRECT_PAGE_INDEXED_BY_Y = "direct page indexed by y"
    DIRECT_PAGE_INDEXED_INDIRECT_BY_X = "direct page indexed indirect by x"
    DIRECT_PAGE_INDIRECT = "direct page indirect"
    DIRECT_PAGE_INDIRECT_LONG = "direct page indirect long"
    DIRECT_PAGE_INDIRECT_LONG_INDEXED_BY_Y = "direct page indirect long indexed by y"
    IMMEDIATE = "immediate"
    IMPLIED = "implied"
    STACK_RELATIVE = "stack relative"
    STACK_RELATIVE_INDIRECT_INDEXED_BY_Y = "stack_relative_indirect_indexed_by_y"

OPS_BY_MENUMONIC_THEN_MODE:dict[str, dict[SnesAddressMode, int]] = {
    "clc": {
        SnesAddressMode.IMPLIED: 0x18,
    },
    "lda": {
        SnesAddressMode.ABSOLUTE_LONG: 0xAF,
        SnesAddressMode.IMMEDIATE: 0xA9,
    },
    "nop": {
        SnesAddressMode.IMPLIED: 0xEA,
    },
    "rep": {
        SnesAddressMode.IMMEDIATE: 0xE2,
    },
    "sec": {
        SnesAddressMode.IMPLIED: 0x38,
    },
    "sei": {
        SnesAddressMode.IMPLIED: 0x78,
    },
    "sep": {
        SnesAddressMode.IMMEDIATE: 0xE2,
    },
    "sta": {
        SnesAddressMode.ABSOLUTE: 0x8D,
        SnesAddressMode.ABSOLUTE_LONG: 0xAF,
    },
    "tcd": {
        SnesAddressMode.IMPLIED: 0x5B
    },
    "xce": {
        SnesAddressMode.IMPLIED: 0xFB
    }
}
"""dict[mnemonic, dict[mode, opcode]]"""

class SnesCompiler():
    def __init__(self):
        self.src:AST = AST()
        self.rom:SnesROM = SnesROM()
        self.ram:SnesRAM = SnesRAM()
    
    def helper_start_segment(self, name:str):
        """Start a new code segment"""
        self.ram.state_unknown()
    
    def helper_end_segment(self, name:str):
        pass
    
    def helper_reorder_bytes(self, val:int, size_in_bytes:int) -> list[int]:
        """
        Splits a value into the correct ordering of bytes for 24 bit, 16 bit,
        or 8 bit in the SNES.
        
        The SNES is little-endian. This means that, for example, the values go
        LLHH for a 16 bit hex value. (So 0x00FF becomes 0xFF00.)

        Args:
            val: the value you need to transform
            size_in_bytes: number of bytes you need back

        Returns:
            list[int]: list of input bytes reordered accordingly
        """
        # set up ret
        ret:list[int] = [] * size_in_bytes
        
        # zero out ret just to be safe
        for i in range(len(ret)):
            ret[i] = 0x00
        
        # aight, this isn't too hard thanks to builtins
        swp = list(val.to_bytes(size_in_bytes, "little"))
        for i in range(len(ret)):
            ret[i] = swp[i]
        
        # done
        return ret
    
    def asm_assemble_no_args(self, op:int):
        """
        Inject an operation that's only the operator
        """
        self.rom.inject_next([op])
    
    def asm_assemble_absolute(self, **kwargs):
        # set ourselves up
        mneumonic:str = kwargs.get("mneumonic", "NOP")
        mneumonic = mneumonic.lower()
        
        mode:SnesAddressMode = kwargs.get("mode", SnesAddressMode.IMPLIED)
        
        address:int = kwargs.get("address", 0x0000)
        address_bytes:list[int] = self.helper_reorder_bytes(address, 2)
        
        opcode:int = OPS_BY_MENUMONIC_THEN_MODE[mneumonic][mode]
        
        # put it all together
        asm:list[int] = [opcode, address_bytes[0], address_bytes[1]]
        
        # inject
        self.rom.inject_next(asm)
        
    def asm_assemble_absolute_long(self, **kwargs):
         # set ourselves up
        mneumonic:str = kwargs.get("mneumonic", "NOP")
        mneumonic = mneumonic.lower()
        
        mode:SnesAddressMode = kwargs.get("mode", SnesAddressMode.IMPLIED)
        
        address:int = kwargs.get("address", 0x0000)
        address_bytes:list[int] = self.helper_reorder_bytes(address, 2)
        
        bank:int = kwargs.get("bank", 0x00)
        
        opcode:int = OPS_BY_MENUMONIC_THEN_MODE[mneumonic][mode]
        
        # put it all together
        asm:list[int] = [opcode, address_bytes[0], address_bytes[1], bank]
        
        # inject
        self.rom.inject_next(asm)
    
    def asm_assemble_immediate(self, **kwargs):
        status_reg = self.ram._cpu_registers._processor_status
        
        # figure out our addressing width
        width:int = 1
        
        if (status_reg.emulation is not None):
            if (status_reg.emulation == 0):
                # native mode
                if (status_reg.m is not None):
                    if (status_reg.m == 1):
                        # 16 bit addressing?
                        width = 2

                # x is zero?
                if (self.ram._cpu_registers._x_index is not None):
                    if (self.ram._cpu_registers._x_index == 0):
                        # 16 bit addressing?
                        width = 2
        
        # aight, swing it
        mneumonic:str = kwargs.get("mneumonic", "NOP")
        mneumonic = mneumonic.lower()
        
        mode:SnesAddressMode = kwargs.get("mode", SnesAddressMode.IMPLIED)
        
        # certain mneumonics are always 8 bit
        if (mneumonic == "rep"):
            width = 1
        
        address:int = kwargs.get("address", 0x0000)
        address_bytes:list[int] = self.helper_reorder_bytes(address, width)
        
        opcode:int = OPS_BY_MENUMONIC_THEN_MODE[mneumonic][mode]
        
        # put it all together
        asm:list[int] = [opcode]
        
        for i in range(len(address_bytes)):
            asm.append(address_bytes [i])
        
        # inject
        self.rom.inject_next(asm)
        
    def asm_assemble_implied(self, **kwargs):
        # TODO: Mode 1
        # TODO: Mode 2
        # TODO: Mode 3
        mneumonic:str = kwargs.get("mneumonic", "NOP")
        mneumonic = mneumonic.lower()
        
        mode:SnesAddressMode = kwargs.get("mode", SnesAddressMode.IMPLIED)
        opcode:int = OPS_BY_MENUMONIC_THEN_MODE[mneumonic][mode]
        
        self.rom.inject_next([opcode])

    
    def asm_clc(self) -> None:
        """
        Clear the carry flag
        """
        self.asm_assemble_implied(mneumonic="clc")
        self.ram._cpu_registers._processor_status.carry = 0
    
    def asm_lda(self, val:int, *, bank:int|None = None, mode:SnesAddressMode=SnesAddressMode.IMMEDIATE, val_length_in_bytes:int|None = None,) -> None:
        """
        Load a value into the accumulator with mode
        """
        raise NotImplementedError()
        if (mode == SnesAddressMode.ABSOLUTE_LONG):
            # bank is required
            if (bank is None):
                raise ValueError("Bank must be set!")
            else:
                # convert
                val_bytes:list[int] = self.helper_reorder_bytes(val, 2)
            
                # assemble
                _asm:list[int] = [0xAF, bank, val_bytes[0], val_bytes[1]]
                
                # inject
                self.rom.inject_next(_asm)

        elif (mode == SnesAddressMode.IMMEDIATE):
            # we need to figure out if the val is 8 or 16 bit
            val_bytes:list[int] = []
            val_len:int = 1 # in bytes
            
            # could try pulling the val length, right?
            if (val_length_in_bytes is not None):
                val_len = val_length_in_bytes
            else:
                # let's guess
                if (val < 0xFF):
                    # 1 byte?
                    val_len = 1
                else:
                    # 2 bytes?
                    val_len = 2
            
            # build val bytes
            val_bytes:list[int] = self.helper_reorder_bytes(val, val_len)
            
            # assemble the op
            # opcode A9 for immediate mode so
            _asm:list[int] = [] * (len(val_bytes) + 1)
            _asm[0] = 0xA9
            for i in range(len(val_bytes)):
                _asm[i+1] = val_bytes[i]
            
            # and now we can inject it
            self.rom.inject_next(_asm)
        
        else:
            raise NotImplementedError()
    
    def asm_rep(self, mask:int) -> None:
        """
        Reset status bits.
        
        The mask is a set of bits corrosponding to which status bit(s) to set to
        zero.
        """
        # assemble
        self.asm_assemble_immediate(mneumonic="rep", address=mask)
        
        # use what we know about the CPU to set it up
        status = self.ram._cpu_registers._processor_status
        
        # carry
        if (mask & 0x01):
            status.carry = 0
        
        # zero
        if (mask & 0x02):
            status.zero = 0
        
        # IRQ disable
        if (mask & 0x04):
            status.irq_disable = 0
        
        # decimal mode
        if (mask & 0x08):
            status.decimal_mode = 0
        
        # index register select
        if (mask & 0x10):
            status.index_register_select = 0
        
        # memory / accumulator select
        if (mask & 0x20):
            status.memory_accumulator_select = 0
        
        # overflow
        if (mask & 0x40):
            status.overflow = 0
        
        # negative
        if (mask & 0x80):
            status.negative = 0
    
    def asm_sta(self, val:int, *, bank:int|None = None, mode:SnesAddressMode=SnesAddressMode.IMMEDIATE, val_length_in_bytes:int|None = None,) -> None:
        """Store accumulator"""
        raise NotImplementedError
        if (mode == SnesAddressMode.ABSOLUTE):
            val_bytes:list[int] = self.helper_reorder_bytes(val, 2)
            self.rom.inject_next([0x8D, val_bytes[0], val_bytes[1]])
        if (mode == SnesAddressMode.ABSOLUTE_LONG):
            # bank is required
            if (bank is None):
                raise ValueError("Bank must be set!")
            else:
                # convert
                val_bytes:list[int] = self.helper_reorder_bytes(val, 2)
            
                # assemble
                _asm:list[int] = [0xAF, bank, val_bytes[0], val_bytes[1]]
                
                # inject
                self.rom.inject_next(_asm)
    def asm_tcd(self) -> None:
        """
        Transfer accumulator to direct page register
        """
        self.asm_inject_no_args(0x5B)
    
    def asm_sec(self) -> None:
        """
        Set the carry flag
        """
        self.asm_inject_no_args(0x38)
    
    def asm_sei(self) -> None:
        """
        Set interrupt
        """
        self.asm_inject_no_args(0x78)
    
    def asm_sep(self, nvmdizc:int) -> None:
        """
        Set status bits
        """
        # TODO: optimization - see if only one bit is set and use more efficient
        #       op if available.
        
        self.rom.inject_next([0xE2, nvmdizc])
    
    def asm_xce(self) -> None:
        """
        Exchanges values of carry and emulation bits.
        """
        self.asm_inject_no_args(0xFB)
    
    def macro_set_mode_emulated(self) -> None:
        """
        Standard setting to set the emulation mode of the SNES processor
        """
        self.asm_sec()
        self.asm_xce()
    
    def macro_set_mode_native(self) -> None:
        """
        Standard setting to set the native mode of the SNES processor
        """
        self.asm_clc()
        self.asm_xce()
    
    def builtin_init(self) -> None:
        self.helper_start_segment("SNES init")
        
        # TODO: Set address
        self.asm_sei()
        self.macro_set_mode_native()
        self.asm_rep(0x30)
        self.asm_lda(0x0000, mode=SnesAddressMode.IMMEDIATE, val_length_in_bytes=2)
        self.asm_sep(0x20)
        self.asm_lda(0x80, mode=SnesAddressMode.IMMEDIATE, val_length_in_bytes=1)
        self.asm_sta(0x2100, mode=SnesAddressMode.IMMEDIATE)
        self.asm_lda(0x00, mode=SnesAddressMode.IMMEDIATE, val_length_in_bytes=1)
        self.asm_sta(0x4200, mode=SnesAddressMode.IMMEDIATE)
        self.asm_lda(0x0200, bank=0x7E, mode=SnesAddressMode.ABSOLUTE_LONG)
        
        # TODO: BEQ
        self.rom.inject_next([0xF0, 0xFB])
        
        self.asm_lda(0x00, mode=SnesAddressMode.IMMEDIATE, val_length_in_bytes=1)
        
        # TODO: STA 24 bit
        self.rom.inject_next([0x8F, 0x00, 0x02, 0x7E])
        
        # TODO: JML 24 bit
        self.rom.inject_next([0x5C, 0x00, 0x80, 0x01])
        
        self.helper_end_segment("SNES init")
        
    def compile(self):
        self.rom = SnesROM()
        
        # set the reset vector?
        self.rom.inject_direct(0x7FFC, [0x00, 0x80])
        
        # set start
        self.rom.current_address = 0x8000
        self.builtin_init()
        
        # try outputting rom
        self.rom.write("grey.smc")