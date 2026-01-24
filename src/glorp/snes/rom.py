from enum import Enum
from math import log2

class SnesROMType(Enum):
    LOROM_FAST = "LoROM fast"
    # nothing else is supported ATM

class SnesROM:
    def __init__(self, size_in_mb:int = 4, type_:SnesROMType=SnesROMType.LOROM_FAST, has_smc_header=False):
        self._bin:bytearray = bytearray(size_in_mb * 1024 * 1024)
        self._romtype:SnesROMType = type_
        self._header_offset:int = 0x00000000
        self._title_offset:int = 0x00000000
        self._mapping_mode_offset:int = 0x00000000
        self._rom_type_offset:int = 0x00000000
        self._sram_size_offset:int = 0x00000000
        self._region_offset:int = 0x00000000
        self._version_offset:int = 0x00000000
        self._checksum_complement_offset:int = 0x00000000
        self._checksum_offset:int = 0x00000000
        self._current_address:int = 0x00000000
        
        self._occupied_addresses:list[bool] = [False] * len(self._bin)
        
        # blank the cart
        for i in range(len(self._bin)):
            self._bin[i] = 0x00
        
        # set up rom
        if (type_ == SnesROMType.LOROM_FAST):
            # 0x7fff and then last 64 bytes
            self._header_offset              = 0x7FC0
            self._title_offset               = 0x7FC0
            self._mapping_mode_offset        = 0x7FD5
            self._rom_type_offset            = 0x7FD6
            self._rom_size_offset            = 0x7FD7
            self._sram_size_offset           = 0x7FD8
            self._region_offset              = 0x7FD9
            self._version_offset             = 0x7FDB
            self._checksum_complement_offset = 0x7FDC
            self._checksum_offset            = 0x7FDE
            
            # there's a fixed value I have to set here
            self.inject_direct(0x7FDA, [33])
            
            # TODO: make these properties and set them correctly
            
            # title
            _t:list[int] = []
            for chr in "titleTITLE&titleTITLE":
                _t.append(ord(chr))
            
            self.inject_direct(self._title_offset, _t)
    
            # mapping mode
            self.inject_direct(self._mapping_mode_offset, [0x30])
    
            # rom type
            # rom, ram, battery - "battery backed save"
            self.inject_direct(self._rom_type_offset, [0x02])
            
            # ROM size
            self.inject_direct(self._rom_size_offset, [int(log2(len(self._bin) / 1024))])
            
            # SRAM size - literally I just set the max here
            self.inject_direct(self._sram_size_offset, [0x07])
            
            # region - we'll just set USA for now
            # TODO: enable setting this to Europe to make my foggylanders happy
            self.inject_direct(self._region_offset, [0x01])
            
            # TODO: try to locate the ability to care about Version
            
            # TODO: Checksum rom
    
    def inject_direct(self, address:int, values:list[int], only_if_empty:bool=True) -> None:
        for i in range(len(values)):
            # empty check
            if (only_if_empty and self._occupied_addresses[address + i]):
                    raise ValueError(f"Tried to write to occupied address: {hex(int(address + i))}")
            
            # write and throw occupied flag
            self._bin[address + i] = values[i]
            self._occupied_addresses[address + i] = True

    def inject_next(self, values:list[int]) -> None:
        self.inject_direct(self._current_address, values)
        self._current_address += len(values)
    
    def write(self, path:str):
        with open(path, "wb") as out:
            out.write(self._bin)
    
    @property
    def current_address(self) -> int:
        return self._current_address
    
    @current_address.setter
    def current_address(self, val:int) -> None:
        self._current_address = val