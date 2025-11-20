from enum import Enum
from xml.etree.ElementTree import Element, SubElement, tostring
from typing import Optional, TYPE_CHECKING
from FluentLabware import LabwareType, Nest_position

if TYPE_CHECKING:
    from Protocol import Protocol


class TecanWorktableScriptGenerator:
    def __init__(self, protocol: Optional['Protocol'] = None):
        """
        初始化工作台指令生成器
        
        Args:
            protocol (Protocol, optional): 协议实例，用于链式调用
        """
        self.protocol = protocol
        
        # XML 生成常量
        self.DEFAULT_BOOL = "False"
        self.DEFAULT_LINE_NUMBER = "1"
        self.SCRIPT_GROUP_LINE_NUMBER = "0"
        self.PREFIX = "B;"
    
    def _execute_command(self, xml_command: str) -> 'TecanWorktableScriptGenerator':
        """
        执行命令：将 XML 添加到协议或返回字符串
        
        Args:
            xml_command (str): 生成的 XML 指令
            
        Returns:
            TecanWorktableScriptGenerator: 返回自身支持链式调用，或字符串（向后兼容）
        """
        if self.protocol:
            self.protocol.add_command(xml_command)
            return self
        else:
            # 向后兼容：直接返回 XML 字符串
            return xml_command

    def _create_base_structure(self):
        """Create the basic XML structure common to all commands."""
        script_group = Element("ScriptGroup")
        objects = SubElement(script_group, "Objects")
        self._add_scriptgroup_metadata(script_group)
        return script_group, objects

    def _add_scriptgroup_metadata(self, parent):
        """Add common ScriptGroup metadata."""
        SubElement(parent, "Name")
        SubElement(parent, "IsBreakpoint").text = self.DEFAULT_BOOL
        SubElement(parent, "IsDisabledForExecution").text = self.DEFAULT_BOOL
        SubElement(parent, "LineNumber").text = self.SCRIPT_GROUP_LINE_NUMBER

    def _add_programming_statement(self, parent):
        """Add common programming statement data."""
        programming_data = SubElement(parent, "Data",
                                      Type="Tecan.Core.Scripting.Programming.ProgrammingStatementBaseDataV1")
        programming_base = SubElement(programming_data, "ProgrammingStatementBaseDataV1")

        SubElement(programming_base, "IsBreakpoint").text = self.DEFAULT_BOOL
        SubElement(programming_base, "IsDisabledForExecution").text = self.DEFAULT_BOOL
        SubElement(programming_base, "LineNumber").text = self.DEFAULT_LINE_NUMBER

    def _add_light_statement(self, parent, light_type):
        """Add common light statement data."""
        light_elem = SubElement(parent, f"{light_type}Statement")

        SubElement(light_elem, "IsBreakpoint").text = self.DEFAULT_BOOL
        SubElement(light_elem, "IsDisabledForExecution").text = self.DEFAULT_BOOL
        SubElement(light_elem, "LineNumber").text = self.DEFAULT_LINE_NUMBER

    def AddLabware(
            self,
            LabwareType: LabwareType,
            LabwareLabel: str,
            Location: Nest_position,
            Position: int | str,
            Rotation: int = 0,
            HasLid: bool = False
            ):
        """
        添加耗材到工作台 (支持链式调用)

        Args:
            LabwareType: 耗材类型枚举 (如 LabwareType.WELL_96_FLAT)
            LabwareLabel (str): 耗材标签 (如 "96MP[001]")
            Location: 位置枚举 (如 Nest_position.Nest61mm_Pos)
            Position (int | str): 位置编号
            Rotation (int): 旋转角度，默认 0
            HasLid (bool): 是否有盖子，默认 False

        Returns:
            TecanWorktableScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
        """
        # 验证枚举类型
        if isinstance(LabwareType, Enum):
            labware_type_value = LabwareType.value
        else:
            raise ValueError(f"Invalid LabwareType: {LabwareType}")
        if isinstance(Location, Enum):
            labware_location = Location.value
        else:
            raise ValueError(f"Invalid Location: {Location}")

        script_group, objects = self._create_base_structure()

        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Worktable.Data.AddLabwareDataV1")
        add_labware = SubElement(object_elem, "AddLabwareDataV1")

        # Add labware parameters
        SubElement(add_labware, "LabwareType").text = labware_type_value
        SubElement(add_labware, "LabwareLable").text = LabwareLabel
        SubElement(add_labware, "Location").text = labware_location
        SubElement(add_labware, "Position").text = str(Position)
        SubElement(add_labware, "Rotation").text = str(Rotation)
        SubElement(add_labware, "HasLid").text = str(HasLid).lower()

        self._add_programming_statement(add_labware)

        xml_command = self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def add_labware(self, labware_type: LabwareType, label: str, location: Nest_position, 
                   position: int | str, rotation: int = 0, has_lid: bool = False):
        """
        添加耗材 (链式调用友好的方法名)
        
        Args:
            labware_type: 耗材类型枚举
            label (str): 耗材标签
            location: 位置枚举
            position: 位置编号
            rotation (int): 旋转角度
            has_lid (bool): 是否有盖子
            
        Returns:
            TecanWorktableScriptGenerator: 支持链式调用
        """
        return self.AddLabware(labware_type, label, location, position, rotation, has_lid)

    def RemoveLabware(self, LabwareName:str)-> str:
        """
        Generate XML script for removing labware from worktable.

        Args:
            LabwareName (str): Labware name to remove (e.g., "96 Well Flat[001]")

        Returns:
            str: Compact XML string with prefix
        """
        script_group, objects = self._create_base_structure()

        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Worktable.Data.RemoveLabwareDataV1")
        remove_labware = SubElement(object_elem, "RemoveLabwareDataV1")

        SubElement(remove_labware, "LabwareName").text = LabwareName
        self._add_programming_statement(remove_labware)

        return self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')

    def InteriorLightOn(self):
        """
        Generate XML script for turning interior light on.

        Returns:
            str: Compact XML string with prefix
        """
        script_group, objects = self._create_base_structure()

        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Statements.InteriorLightOnStatement")
        self._add_light_statement(object_elem, "InteriorLightOn")

        return self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')

    def InteriorLightOff(self):
        """
        Generate XML script for turning interior light off.

        Returns:
            str: Compact XML string with prefix
        """
        script_group, objects = self._create_base_structure()

        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Statements.InteriorLightOffStatement")
        self._add_light_statement(object_elem, "InteriorLightOff")

        return self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')