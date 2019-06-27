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