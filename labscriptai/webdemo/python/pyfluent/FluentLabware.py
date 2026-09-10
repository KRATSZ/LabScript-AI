from enum import Enum


class MCA384HeadAdapter:
    def __init__(self, Label):
        self.Label = Label
        if "EVA" in Label.upper():
            self.ID = "DiTi96.ExtVol"
            self.Name="EVA (Extended Volume)"
        if "96 MCA96 TIPS" in Label.upper():
            self.ID = "DiTi96"
            self.Name="96 MCA96 Tips"
        if "96 MCA384 TIPS" in Label.upper():
            self.ID = "DiTi96.Combo"
            self.Name="96 MCA384 Tips"
        if "96 MCA384 TIPS" in Label.upper():
            self.ID = "DiTi96.Combo"
            self.Name="96 MCA384 Tips"
        if "384 TIPS COMBO" in Label.upper():
            self.ID = "DiTi384.Combo"
            self.Name="384 Tips Combo (Partial Tips)"



class LabwareType(Enum):
    WELL_24_FLAT = "24 Well Flat"
    WELL_96_FLAT = "96 Well Flat"
    WELL_96_Round = "96 Well Round"
    DeepWELL_500ul_96 = "96 Deep Well 0.5ml"
    DeepWELL_1ml_96 = "96 Deep Well 1ml"
    DeepWELL_2ml_96 = "96 Deep Well 2ml"

    PCR_96 = "96 Well Skirted PCR"

    WELL_384_FLAT = "384 Well Flat"

    SBS_Trough="300ml SBS"

    FCA_1000ul="FCA, 1000ul"
    FCA_1000ul_SBS = "FCA, 1000ul SBS"

    FCA_200ul = "FCA, 200ul"
    FCA_200ul_SBS = "FCA, 200ul SBS"

    FCA_50ul = "FCA, 50ul"
    FCA_50ul_SBS = "FCA, 50ul SBS"

    FCA_10ul = "FCA, 10ul"
    FCA_10ul_SBS = "FCA, 10ul SBS"

    MCA_200ul="MCA96, 200ul, Box"
    MCA_50ul="MCA96, 50ul, Box"


    # 添加其他允许的labware类型

    @classmethod
    def has_value(cls, value):
        return value in set(item.value for item in cls)



class Nest_position(Enum):
    Nest61mm_Pos = "Nest61mm_Pos"
    Nest7mm_Pos="Nest7mm_Pos"
    Hotel_4Nest="Hotel_4Nest"
    Hotel_3Nest_Pos_1_8_15="Hotel_3Nest_Pos_1_8_15"
    HotelDWP_5Pos="HotelDWP_Pos"
    HotelMP_9Pos="HotelMP_Pos"
    FCA_DiTiTray_Site="FCA_DiTiTray_Site"
    Trough_100ml="Trough_100ml"
    CPAC_PCR_Pos="CPAC_PCR_Pos"
    ThemoShake_PCR_Pos="ThemoShake_PCR_Pos"
    @classmethod
    def has_value(cls, value):
        return value in set(item.value for item in cls)