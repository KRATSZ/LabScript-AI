from enum import Enum


class LiquidClass(Enum):
    Water_Free_Single = "Water Free Single"
    Water_Free_Multi = "Water Free Multi"
    Ethanol_Free_Single = "Ethanol Free Single"
    Ethanol_Free_Multi = "Ethanol Free Multi"
    DMSO_Free_Single = "DMSO Free Single"
    DMSO_Free_Multi = "DMSO Free Multi"
    MasterMix_Free_Single = "MasterMix Free Single"
    MasterMix_Free_Multi = "MasterMix Free Multi"
    Water_Mix="Water Mix"
    Empty_Tip="Empty Tip"
    MCA_Water_Contact_Single="Water Contact Wet Single"
    MCA_Water_Contact_Multi = "Water Contact Wet Multi"

    @classmethod
    def has_value(cls, value):
        return value in set(item.value for item in cls)