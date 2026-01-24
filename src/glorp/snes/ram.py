from enum import Enum

class RAMStatus(Enum):
    UNKNOWN = "unknown"
    """We don't know the status of the RAM."""
    
    EMPTY = "empty"
    """The RAM has a known status of empty"""
    
    FILLED = "filled"
    """The RAM has a known status of in-use """

class RAMValueStatus(Enum):
    UNKNOWN = "unknown"
    """We can't be sure of the value of the RAM right now"""
    
    KNOWN = "known"
    """We know the value of the RAM now"""

class RAMByte():
    def __init__(self, value=0x00):
        self._status:RAMStatus = RAMStatus.UNKNOWN
        self._value:int = 0x00
        self._value_status:RAMValueStatus = RAMValueStatus.UNKNOWN
        self._mirrors:set[RAMByte] = set()
        self._recursive_guard:bool = False
        
        # set value
        self.value = value
        
        # set statuses again just to be sure
        self.status = RAMStatus.UNKNOWN 
    
    @property
    def status(self) -> RAMStatus:
        return self._status
    
    @status.setter
    def status(self, val:RAMStatus) -> None:
        if (not self._recursive_guard):
            self._recursive_guard = True
            
            self._status = val
            
            for mirror in self._mirrors:
                mirror.status = val
        
            self._reset_recursive_guard()
    
    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, val:int) -> None:
        if (not self._recursive_guard):
            self._recursive_guard = True
            
            # constraints
            if ((val < 0x00) or (val > 255)):
                raise ValueError("Byte must be between 0x00 and 0xFF (0 and 255)")
            
            # now we set it
            self._value = val
            self._status = RAMStatus.FILLED
            self._value_status = RAMValueStatus.KNOWN
        
            for mirror in self._mirrors:
                mirror.value = val
            
            self._reset_recursive_guard()
    
    @property
    def value_status(self) -> RAMValueStatus:
        return self._value_status
    
    @value_status.setter
    def value_status(self, val:RAMValueStatus) -> None:
        if (not self._recursive_guard):
            self._recursive_guard = True
            
            self._value_status = val
            
            for mirror in self._mirrors:
                mirror.value_status = val
        
            self._reset_recursive_guard()
    
    def _reset_recursive_guard(self):
        # only reset if it's not been reset yet
        if (self._recursive_guard):
            self._recursive_guard = False
            
            for mirror in self._mirrors:
                mirror._reset_recursive_guard()
    
    def add_mirror(self, other:"RAMByte"):
        if other is not self:
            self._mirrors.add(other)
            other._mirrors.add(self)
    
    def delete(self):
        """
        Just marks this byte as empty.
        
        Does not set this byte's value as zero. That's because it's realistic in
        practice.
        """
        self.status = RAMStatus.EMPTY
        self.value_status = RAMValueStatus.UNKNOWN
    
    def reset(self):
        """
        Just marks this byte as unknown.
        
        Does not set this byte's value as zero. That's because it's realistic in
        practice.
        """
        self.status = RAMStatus.UNKNOWN
        self.value_status = RAMValueStatus.UNKNOWN

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
        
    @classmethod
    def from_segment(cls, source:"RAMSegment", address:int, length:int) -> "RAMSegment":
        ret:RAMSegment = cls(address, length)
        swp:list[RAMByte] = source.get_byte_handles(address, length)
        ret.set_byte_handles(address, swp)
        return ret

class SNESSystemRam():
    def __init__(self):
        self.all:RAMSegment = RAMSegment(0, (0xFFFFFF + 1))
        
        # now we can just get all the banks together
        self.banks:list[RAMSegment] = []
        
        for i in range(256):
            bank_start:int = i * 0x010000
            
            bank:RAMSegment = RAMSegment.from_segment(self.all, bank_start, 0x10000)
            self.banks.append(bank)
        
        # wram - basic setup
        self.wram_all:RAMSegment     = RAMSegment.from_segment(self.all, 0x7E0000, 0x10000)
        self.wram_stack:RAMSegment   = RAMSegment.from_segment(self.all, 0x7E0000, 0x1FFF + 1)
        self.wram_scratch:RAMSegment = RAMSegment.from_segment(self.all, 0x7E2000, 0xDFFF + 1)
        
        # wram - mirroring - all
        for byte_address in range(0x10000):
            left:RAMByte = self.all.get_byte(0x7E0000 + byte_address)
            right:RAMByte = self.all.get_byte(0x7F0000 + byte_address)
        
            left.add_mirror(right)
        
        # wram - mirroring - stack
        for byte_address in range(0x2000):
            mirror_bytes:list[RAMByte] = []
            
            for bank_val in range(0x00, 0x40):
                mirror_addr:int = (bank_val * 0x10000) + byte_address
                mirror_bytes.append(self.all.get_byte(mirror_addr))
            
            for bank_val in range(0x7E, 0xC0):
                mirror_addr:int = (bank_val * 0x10000) + byte_address
                mirror_bytes.append(self.all.get_byte(mirror_addr))
            
            for left_idx in range(len(mirror_bytes) - 1):
                left:RAMByte = mirror_bytes[left_idx]
                right:RAMByte = mirror_bytes[left_idx + 1]
                left.add_mirror(right)
        
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