from enum import Enum

class Provider(Enum):
    NETFLIX = "Netflix"
    DISNEY_PLUS = "Disney Plus"
    AMAZON_PRIME_VIDEO = "Amazon Prime Video"
    AMAZON_VIDEO = "Amazon Video"
    WOW = "WOW"
    PARAMOUNT_PLUS = "Paramount Plus"
    APPLE_TV = "Apple TV"
    APPLE_TV_PLUS = "Apple TV+"
    MAGENTA_TV = "MagentaTV"
    MAGENTA_TV_PLUS = "Magenta TV+"
    
class FreeProvider(Enum):
    NETFLIX = "Netflix"
    DISNEY_PLUS = "Disney Plus"
    AMAZON_PRIME_VIDEO = "Amazon Prime Video"
    #AMAZON_VIDEO = "Amazon Video"
    WOW = "WOW"
    PARAMOUNT_PLUS = "Paramount Plus"
    #APPLE_TV = "Apple TV"
    APPLE_TV_PLUS = "Apple TV+"
    #MAGENTA_TV = "MagentaTV"
    MAGENTA_TV_PLUS = "Magenta TV+"    
    
class PaymentTypes(Enum):
    FREE = "free"
    RENT = "rent"
    #BUY = "buy"