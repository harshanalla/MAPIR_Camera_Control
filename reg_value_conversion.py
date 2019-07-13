from codecs import decode
import struct
import ast

def convert_imu_register_value(sign, high_byte, low_byte):
    unsigned_value = (256*high_byte + low_byte)
    if sign == 1:
        unsigned_value *= -1
    return unsigned_value

# def convertUnsignedToSignedFloat(self, unsignedValue):
#   isNegative = (unsignedValue>>15)&1
#   if isNegative:
#       return (0x7FFF&unsignedValue) -  2**15
#   else:
#       return unsignedValue

def convert_acceleration_reg_values_to_float(reg_values):
    binary = convert_acceleration_reg_values_to_binary(reg_values)
    return convert_binary_to_float(binary)

def convert_acceleration_reg_values_to_binary(reg_values):
    binary = reg_values[3]*(2**24) + reg_values[2]*(2**16)+ reg_values[1]*(2**8)+ reg_values[0]
    return binary

def convert_binary_to_float(binary):
    binaryString = bin(binary)[2:]
    f = int(binaryString, 2)
    return struct.unpack('f', struct.pack('I', f))[0]