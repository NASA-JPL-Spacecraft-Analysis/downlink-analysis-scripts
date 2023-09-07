from enum import Enum

class ValueType(Enum):
    MEASURED = 'MEASURED'
    PREDICTED = 'PREDICTED'
    DERIVED = 'DERIVED'

class Volatility(Enum):
    VOLATILE = 'VOLATILE'
    NON_VOLATILE = 'NON_VOLATILE'

enum_classes = {'valueType': ValueType, 'volatility': Volatility}