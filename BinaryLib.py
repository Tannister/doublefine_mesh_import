import struct
from pathlib import Path

class Endian():
    Native         = '@'
    NativeStandard = '='
    Little         = '<'
    Big            = '>'
    Network        = '!'

class CType():
    _format = ''
    _size   = 0
    
    @staticmethod
    def convert(data):
        return data

class Char():
    _format = 'c'
    _size   = 1
    
    @staticmethod
    def convert(data):
        ret = ""
        for c in data:
            ret = ret + chr(ord(c))
        return ret

class Bool():
    _format = '?'
    _size   = 1
    
    @staticmethod
    def convert(data):
        return data


class Int8():
    _format = 'b'
    _size   = 1
    
    @staticmethod
    def convert(data):
        return data

class UInt8():
    _format = 'B'
    _size   = 1
    
    @staticmethod
    def convert(data):
        return data
        
class Int16():
    _format = 'h'
    _size   = 2
    
    @staticmethod
    def convert(data):
        return data

class UInt16():
    _format = 'H'
    _size   = 2
    
    @staticmethod
    def convert(data):
        return data

class Int32():
    _format = 'i'
    _size   = 4
    
    @staticmethod
    def convert(data):
        return data

class UInt32():
    _format = 'I'
    _size   = 4
    
    @staticmethod
    def convert(data):
        return data

class Int64():
    _format = 'q'
    _size   = 8
    
    @staticmethod
    def convert(data):
        return data

class UInt64():
    _format = 'Q'
    _size   = 8
    
    @staticmethod
    def convert(data):
        return data

class Float16():
    _format = 'e'
    _size   = 2
    
    @staticmethod
    def convert(data):
        return data

class Float32():
    _format = 'f'
    _size   = 4
    
    @staticmethod
    def convert(data):
        return data

class Float64():
    _format = 'd'
    _size   = 8
    
    @staticmethod
    def convert(data):
        return data

class BinaryFile():
    def __init__(self, file, endian=Endian.Native):
    
        filepath = None
        if(isinstance(file, str)):
            filepath = Path(file)
        if(isinstance(file, Path)):
            filepath = file
        
        if(filepath is None):
            raise Exception("Invalid FilePath !")
        if(not filepath.exists()):
            raise Exception("File does not exist !")
            
        self._handle = open(filepath, 'rb')
        self._endian = endian
        
        self.seek = self._handle.seek
        self.tell = self._handle.tell
    
    def close(self):
        self._handle.close()
        self = None
    
    def _unpack(self, data):
        if(isinstance(data, tuple)):
            if(len(data)==1):
                data, = data
        return data
    
    def read(self, ctype, count):
        return self._unpack(
            ctype.convert(
                struct.unpack(
                    self._endian + ctype._format * count,
                    self._handle.read(ctype._size * count)
                )
            )
        )
    
    def find_next(self, ctype, value):
        current_offset = self.tell()
        
        while(True):
            read_val = self.read(ctype, 1)
            if(read_val == value):
                found_offset = self.tell()
                self.seek(current_offset)
                return found_offset
            
            if(read_val == None):
                self.seek(current_offset)
                return None