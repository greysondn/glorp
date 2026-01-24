from enum import Enum

class RAMStatus(Enum):
    UNKNOWN = "unknown"
    """We don't know the status of the RAM."""
    
    EMPTY = "empty"
    """The RAM has a known status of empty"""
    
    FILLED = "filled"
    """The RAM has a known status of in-use """

class RAMByte():
    def __init__(self, value=0x00):
        self._status:RAMStatus = RAMStatus.UNKNOWN
        self._value:int = 0x00
        
        # set value
        self.value = value
        
        # set status again just to be sure
        self.status = RAMStatus.UNKNOWN 
    
    @property
    def status(self) -> RAMStatus:
        return self._status
    
    @status.setter
    def status(self, val:RAMStatus) -> None:
        self._status = val
    
    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, val:int) -> None:
        # constraints
        if ((val < 0x00) or (val > 255)):
            raise ValueError("Byte must be between 0x00 and 0xFF (0 and 255)")
        
        # now we set it
        self._value = val
        self._status = RAMStatus.FILLED
    
    def delete(self):
        """
        Just marks this byte as empty.
        
        Does not set this byte's value as zero. That's because it's realistic in
        practice.
        """
        self.status = RAMStatus.EMPTY
    
    def reset(self):
        """
        Just marks this byte as unknown.
        
        Does not set this byte's value as zero. That's because it's realistic in
        practice.
        """
        self.status = RAMStatus.UNKNOWN

class RAMSegment():
    def __init__(self, start:int, length:int):
        self.start:int = start
        """The start address of this in memory."""
        self.length:int = length
        """The end address of this in memory."""
        
        self.bytes:list[RAMByte] = [RAMByte()] * length
        """The internal data from this."""
    
    def _offset_address(self, address:int) -> int:
        return address - self.start
    
    def get_byte_handles(self, start:int, length:int) -> list[RAMByte]:
        return self.bytes[start:(start+length)]
    
    def set_byte_handles(self, start:int, bytes_:list[RAMByte]):
        for i in range(len(bytes_)):
            self.bytes[start + i] = bytes_[i]
    
    def allocate(self, address:int, length:int) -> int:
        raise NotImplementedError
    
    def allocate_any(self, length:int) -> int:
        # allocate this in first worst style
        raise NotImplementedError
    
    def deallocate(self, address:int, length:int) -> None:
        for i in range(length):
            self.bytes[self._offset_address(address + i)].delete()
    
    def get_byte(self, address:int) -> RAMByte:
        return self.bytes[self._offset_address(address)]
    
    def get_value(self, address:int) -> int:
        return self.bytes[self._offset_address(address)].value
    
    def set_value(self, address:int, value:int) -> None:
        self.bytes[self._offset_address(address)].value = value
    
class SnesVariable():
    def __init__(self, name:str, start:int, end:int, type_:str):
        self.name = name
        self.start = start
        self.end   = end
        self.type  = type_
    
    @property
    def length(self) -> int:
        return (self.end - self.start)
    
    @property
    def value(self):
        raise NotImplementedError()
    
    @value.setter
    def value(self, val):
        raise NotImplementedError()

class SNESRamSegment():
    def __init__(self, name:str, start:int, end:int):
        self.name   = name
        self.start  = start
        self.end    = end
        self.parents:list[SNESBank] = []
        
    def add_to(self, new_parent:"SNESBank"):
        new_parent.add(self)
        self.parents.append(new_parent)
    
class SNESBank():
    def __init_(self, index:int, start:int, end:int):
        self.index = index
        self.start = start
        self.end   = end
    
        self.segments:dict[str, SNESRamSegment] = {}
        
    def add(self, segment:SNESRamSegment):
        self.segments[segment.name] = segment

class SNESSystemRam():
    def __init__(self):
        # just assemble it in order though
        self._banks:list[SNESBank] = []
        
        # set up segments
        lowram:SNESRamSegment     = SNESRamSegment("lowram",     0x0000, 0x1FFF)
        ppu_apu:SNESRamSegment    = SNESRamSegment("ppu_apu",    0x2000, 0x3FFF)
        controller:SNESRamSegment = SNESRamSegment("controller", 0x4000, 0x41FF)
        cpu_dma:SNESRamSegment    = SNESRamSegment("cpu_dma",    0x4200, 0x5FFF)
        expansion:SNESRamSegment  = SNESRamSegment("expansion",  0x6000, 0x7FFF)
        
        wram_low:SNESRamSegment   = SNESRamSegment("wram_low",   0x2000, 0xFFFF)
        wram_high:SNESRamSegment  = SNESRamSegment("wram_high",  0x0000, 0xFFFF)
        
        # set up banks
        for _ in range(256):
            self._banks.append(SNESBank())
            
        # set up all mirrors of a lot of stuff
        for i in range(0x40):
            self._banks[i].add(lowram)
            self._banks[i].add(ppu_apu)
            self._banks[i].add(controller)
            self._banks[i].add(cpu_dma)
            self._banks[i].add(expansion)
        
        self._banks[0x7E].add(lowram)
        
        for i in range(0x80, 0xC0):
            self._banks[i].add(lowram)
            self._banks[i].add(ppu_apu)
            self._banks[i].add(controller)
            self._banks[i].add(cpu_dma)
            self._banks[i].add(expansion)
        
        # set up wram
        self._banks[0x7E].add(wram_low)
        self._banks[0x7F].add(wram_high)
        
        # set up underlying data
        self._data:bytearray = bytearray(0xFFFFFF)
        self._used:list[bool] = [False] * 0xFFFFFF
        
        # vars
        self._vars:dict[str, SnesVariable] = {}
        
        
        
class SNESProcessStatusRegister():
    def __init__(self):
        self._emulation:int|None = None
        self._carry:int|None = None
        self._zero:int|None = None
        self._irq_disable:int|None = None
        self._decimal_mode:int|None = None
        self._index_register_select:int|None = None
        self._memory_accumulator_select:int|None = None
        self._overflow:int|None = None
        self._negative:int|None = None
    
    def set(self, val:int):
        # carry
        if (val & 0x01):
            self._carry = 1
        else:
            self._carry = 0
        
        # zero
        if (val & 0x02):
            self._zero = 1
        else:
            self._zero = 0
        
        # IRQ disable
        if (val & 0x04):
            self._irq_disable = 1
        else:
            self._irq_disable = 0
        
        # decimal mode
        if (val & 0x08):
            self._decimal_mode = 1
        else:
            self._decimal_mode = 0
        
        # index register select
        if (val & 0x10):
            self._index_register_select = 1
        else:
            self._index_register_select = 0
        
        # memory / accumulator select
        if (val & 0x20):
            self._memory_accumulator_select = 1
        else:
            self._index_register_select = 0
        
        # overflow
        if (val & 0x40):
            self._overflow = 1
        else:
            self._overflow = 0
        
        # negative
        if (val & 0x80):
            self._negative = 1
        else:
            self._negative = 0
    
    def get(self) -> int|None:
        ret:int|None = None
        
        bits:list[int|None] = [
            self._carry,
            self._zero,
            self._irq_disable,
            self._decimal_mode,
            self._index_register_select,
            self._memory_accumulator_select,
            self._overflow,
            self._negative,
        ]
        
        have_none:bool = False
        
        for bit in bits:
            if (bit is None):
                have_none = True
                
        if (not have_none):
            ret = 0
            
            for i in range(len(bits)):
                 ret += (2 ** i) * bits[i]

        return ret

    def state_unknown(self):
        self._carry = None
        self._zero = None
        self._irq_disable = None
        self._decimal_mode = None
        self._index_register_select = None
        self._memory_accumulator_select = None
        self._overflow = None
        self._negative = None
        self._emulation = None
    
    def _validate_bit(self, val:int):
        if ((val != 0) and (val != 1)):
            raise ValueError("You're setting a bit, not an integer.")
    
    @property
    def c(self) -> int|None:
        return self._carry
    
    @property
    def carry(self) -> int|None:
        return self._carry
    
    @carry.setter
    def carry(self, val:int) -> None:
        self._validate_bit(val)
        self._carry = val

    @property
    def d(self) -> int|None:
        return self._decimal_mode

    @property
    def decimal_mode(self) -> int|None:
        return self._decimal_mode
    
    @decimal_mode.setter
    def decimal_mode(self, val:int) -> None:
        self._validate_bit(val)
        self._decimal_mode = val
    
    @property
    def e(self) -> int|None:
        return self._emulation
    
    @property
    def emulation(self) -> int|None:
        return self._emulation

    @emulation.setter
    def emulation(self, val:int) -> None:
        self._validate_bit(val)
        self._emulation = val
    
    @property
    def i(self) -> int|None:
        return self._irq_disable
    
    @property
    def irq_disable(self) -> int|None:
        return self._irq_disable

    @irq_disable.setter
    def irq_disable(self, val:int) -> None:
        self._validate_bit(val)
        self._irq_disable = val
    
    @property
    def m(self) -> int|None:
        return self._memory_accumulator_select
    
    @property
    def memory_accumulator_select(self) -> int|None:
        return self._memory_accumulator_select

    @memory_accumulator_select.setter
    def memory_accumulator_select(self, val:int) -> None:
        self._validate_bit(val)
        self._memory_accumulator_select = val
    
    @property
    def n(self) -> int|None:
        return self._negative
    
    @property
    def negative(self) -> int|None:
        return self._negative

    @negative.setter
    def negative(self, val:int) -> None:
        self._validate_bit(val)
        self._negative = val
    
    @property
    def v(self) -> int|None:
        return self._overflow
    
    @property
    def overflow(self) -> int|None:
        return self._overflow

    @overflow.setter
    def overflow(self, val:int) -> None:
        self._validate_bit(val)
        self._overflow = val
    
    @property
    def x(self) -> int|None:
        return self._index_register_select
    
    @property
    def index_register_select(self) -> int|None:
        return self._index_register_select

    @index_register_select.setter
    def index_register_select(self, val:int) -> None:
        self._validate_bit(val)
        self._index_register_select = val
    
    @property
    def z(self) -> int|None:
        return self._zero

    @property
    def zero(self) -> int|None:
        return self._zero

    @zero.setter
    def zero(self, val:int) -> None:
        self._validate_bit(val)
        self._zero = val

class SnesCPURegisters():
    def __init__(self):
        self._accumulator:int|None = None
        self._x_index:int|None = None
        self._y_index:int|None = None
        self._processor_status:SNESProcessStatusRegister = SNESProcessStatusRegister()
        self._stack:int|None = None
        self._program_counter:int|None = None

    def state_unknown(self):
        self._accumulator = None
        self._x_index = None
        self._y_index = None
        self._stack = None
        self._program_counter = None
        
        self._processor_status.state_unknown()
    
class SnesRAM():
    def __init__(self):
        self._cpu_registers:SnesCPURegisters = SnesCPURegisters()
    
    def state_unknown(self):
        self._cpu_registers.state_unknown()