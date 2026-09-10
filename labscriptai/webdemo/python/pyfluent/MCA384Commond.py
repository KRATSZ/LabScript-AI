from enum import Enum
from xml.etree.ElementTree import Element, SubElement, tostring
from typing import Optional, TYPE_CHECKING
from FluentLabware import MCA384HeadAdapter
from FluentLiquidClass import LiquidClass

if TYPE_CHECKING:
    from Protocol import Protocol, MCAState, InvalidStateException
else:
    try:
        from Protocol import MCAState, InvalidStateException
    except ImportError:
        # 为了向后兼容，如果没有 Protocol 模块，定义简单的状态类
        from enum import Enum, auto
        class MCAState(Enum):
            IDLE = auto()
            ADAPTER_LOADED = auto()
            TIPS_LOADED = auto()
        class InvalidStateException(Exception):
            pass


class TecanMCA384ScriptGenerator:
    def __init__(self, protocol: Optional['Protocol'] = None):
        """
        初始化 MCA384 指令生成器
        
        Args:
            protocol (Protocol, optional): 协议实例，用于链式调用和状态管理
        """
        self.protocol = protocol
        
        # XML 生成常量
        self.DEVICE_ALIAS = "Instrument=1/Device=MCA384:1"
        self.DEFAULT_POSITION = "0"
        self.ADAPTER_TYPE = "DiTiAdapter"
        self.TIP_LAYOUT = {
            "XCount": "12",
            "YCount": "8",
            "XSpacing": "9",
            "YSpacing": "9",
            "SortNumber": "50",
            "MountColumnRowWise": "false"
        }
        
        # 状态管理
        self.state = MCAState.IDLE
        self.current_adapter: Optional[MCA384HeadAdapter] = None
    
    def _validate_state(self, required_state: MCAState, operation_name: str) -> None:
        """
        验证当前状态是否允许执行指定操作
        
        Args:
            required_state (MCAState): 要求的状态
            operation_name (str): 操作名称，用于错误信息
            
        Raises:
            InvalidStateException: 当状态不匹配时
        """
        if self.state != required_state:
            raise InvalidStateException(
                f"错误：无法执行 {operation_name}。"
                f"当前状态: {self.state.name}，要求状态: {required_state.name}"
            )
    
    def _validate_labware_exists(self, labware_label: str) -> None:
        """
        验证耗材是否已定义 (仅在有 protocol 实例时)
        
        Args:
            labware_label (str): 耗材标签
            
        Raises:
            ValueError: 当耗材未定义时
        """
        if self.protocol and labware_label not in self.protocol.get_defined_labware():
            raise ValueError(f"错误：耗材 '{labware_label}' 未定义。请先使用 add_labware() 添加。")
    
    def _execute_command(self, xml_command: str) -> 'TecanMCA384ScriptGenerator':
        """
        执行命令：将 XML 添加到协议或返回字符串
        
        Args:
            xml_command (str): 生成的 XML 指令
            
        Returns:
            TecanMCA384ScriptGenerator: 返回自身支持链式调用，或字符串（向后兼容）
        """
        if self.protocol:
            self.protocol.add_command(xml_command)
            return self
        else:
            # 向后兼容：直接返回 XML 字符串
            return xml_command

    def _validate_adapter(self, adapter):
        """Validate that the adapter is of correct type."""
        if not isinstance(adapter, MCA384HeadAdapter):
            raise ValueError(
                f"Adapterplate must be an instance of MCA384HeadAdapter, but got {type(adapter).__name__}")

    def _create_base_structure(self):
        """Create the basic XML structure common to all commands."""
        script_group = Element("ScriptGroup")
        objects = SubElement(script_group, "Objects")
        self._add_scriptgroup_metadata(script_group)
        return script_group, objects

    def _add_scriptgroup_metadata(self, parent):
        """Add common ScriptGroup metadata."""
        SubElement(parent, "Name")
        SubElement(parent, "IsBreakpoint").text = "False"
        SubElement(parent, "IsDisabledForExecution").text = "False"
        SubElement(parent, "LineNumber").text = "0"

    def _add_common_device_data(self, parent, fluent_sn):
        """Add common device alias and ID information."""
        device_alias_data = SubElement(parent, "Data",
                                       Type="Tecan.Core.Instrument.Helpers.Scripting.DeviceAliasStatementBaseDataV1")
        device_alias = SubElement(device_alias_data, "DeviceAliasStatementBaseDataV1")

        SubElement(device_alias, "Alias", Type="Tecan.Core.Instrument.DeviceAlias.DeviceAlias").text = self.DEVICE_ALIAS

        id_elem = SubElement(device_alias, "ID")
        SubElement(id_elem, "AvailableID").text = f"USB:TECAN,MYRIUS,{fluent_sn}/MCA384:1"

        self._add_script_statement(device_alias)

    def _add_script_statement(self, parent):
        """Add common script statement data."""
        script_data = SubElement(parent, "Data",
                                 Type="Tecan.Core.Scripting.Helpers.ScriptStatementBaseDataV1")
        script_base = SubElement(script_data, "ScriptStatementBaseDataV1")

        SubElement(script_base, "IsBreakpoint").text = "False"
        SubElement(script_base, "IsDisabledForExecution").text = "False"
        SubElement(script_base, "GroupLineNumber").text = "0"
        SubElement(script_base, "LineNumber").text = "1"

    def _add_common_data_v2(self, parent, labware_name=""):
        """Add common ScriptCommandCommonDataV2 structure."""
        common_data = SubElement(parent, "Data",
                                 Type="Tecan.Core.Instrument.Helpers.Scripting.ScriptCommandCommonDataV2")
        common_data_v2 = SubElement(common_data, "ScriptCommandCommonDataV2")

        SubElement(common_data_v2, "LabwareName").text = labware_name
        SubElement(common_data_v2, "LiquidClassVariablesNames")
        SubElement(common_data_v2, "LiquidClassVariablesValues")

        return common_data_v2

    def _add_well_selection_data(self, parent, adapter):
        """Add common well selection data structure."""
        well_selection = SubElement(parent, "Data",
                                    Type="Tecan.Core.Instrument.Devices.Mca._384.Scripting.Data.Mca384ScriptCommandUsingWellSelectionBaseDataV6")
        well_data = SubElement(well_selection, "Mca384ScriptCommandUsingWellSelectionBaseDataV6")

        # Well position parameters
        SubElement(well_data, "WellOffset").text = self.DEFAULT_POSITION
        position_first_tip = SubElement(well_data, "PositionFirstTip")
        point = SubElement(position_first_tip, "Point")
        SubElement(point, "X").text = self.DEFAULT_POSITION
        SubElement(point, "Y").text = self.DEFAULT_POSITION
        SubElement(well_data, "Compartment").text = "1"

        # Adapter plate info
        self._add_adapter_plate(well_data, adapter)

        # Other well parameters
        used_tip = SubElement(well_data, "UsedTip")
        SubElement(used_tip, "UsableTips").text = "All"

        SubElement(well_data, "FirstTipXPosition").text = "1"
        SubElement(well_data, "FirstTipYPosition").text = "1"
        SubElement(well_data, "LastTipXPosition").text = "12"
        SubElement(well_data, "LastTipYPosition").text = "8"

        for param in ["Column", "Row", "RowOffset", "ColumnOffset",
                      "OrientationPhi", "OrientationPsi", "OrientationTheta"]:
            SubElement(well_data, param).text = self.DEFAULT_POSITION

        SubElement(well_data, "SelectedRowsOrColumns")
        SubElement(well_data, "SubsequentPipettingDirectionIsRow").text = "False"
        SubElement(well_data, "LiquidClassVariablesNames")
        SubElement(well_data, "LiquidClassVariablesValues")

        return well_data

    def _add_adapter_plate(self, parent, adapter):
        """Add adapter plate information."""
        adapter_plate = SubElement(parent, "AdapterPlate")
        adapter_data = SubElement(adapter_plate, "AdapterData")

        SubElement(adapter_data, "Name").text = adapter.Name
        SubElement(adapter_data, "Type").text = self.ADAPTER_TYPE
        SubElement(adapter_data, "CanMountTecanDiTis").text = "true"

        for key, value in self.TIP_LAYOUT.items():
            SubElement(adapter_data, key).text = value

        SubElement(adapter_data, "ID").text = f"TOOLTYPE:Mca384.Adapter/TOOLNAME:{adapter.ID}"

        usable_tips = SubElement(adapter_data, "UsableTips")
        SubElement(usable_tips, "UsableTips").text = "All"

    def _add_pipetting_params(self, parent, volume, liquid_class):
        """Add pipetting parameters."""
        SubElement(parent, "LiquidClassName").text = liquid_class
        SubElement(parent, "Volume").text = str(volume)
        SubElement(parent, "IsLiquidClassNameByExpressionEnabled").text = "False"
        SubElement(parent, "LiquidClassNameBySelection").text = liquid_class
        SubElement(parent, "LiquidClassNameByExpression")
        SubElement(parent, "OffsetX").text = self.DEFAULT_POSITION
        SubElement(parent, "OffsetY").text = self.DEFAULT_POSITION

    def _add_partial_tip_data(self, parent, cols="12", rows="8"):
        """Add partial tip command data."""
        partial_tip = SubElement(parent, "Data",
                                 Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384PartialTipCommandBaseDataV1")
        partial_tip_data = SubElement(partial_tip, "Mca384PartialTipCommandBaseDataV1")

        SubElement(partial_tip_data, "PartialColumns").text = cols
        SubElement(partial_tip_data, "PartialRows").text = rows
        SubElement(partial_tip_data, "PartialColumnOffset").text = self.DEFAULT_POSITION
        SubElement(partial_tip_data, "PartialRowsOffset").text = self.DEFAULT_POSITION

        head_position = SubElement(partial_tip_data, "HeadPosition")
        SubElement(head_position, "HeadPositions").text = "Center"

        SubElement(partial_tip_data, "RemoveRack").text = "False"
        SubElement(partial_tip_data, "WasteForDitis")

        return partial_tip_data

    def GetHeadAdapter(self, adapter: MCA384HeadAdapter, fluent_sn: str = None):
        """
        获取 MCA384 头部适配器 (支持链式调用和状态管理)

        Args:
            adapter (MCA384HeadAdapter): 适配器对象，包含 Name 和 ID 属性
            fluent_sn (str, optional): 设备序列号，如果未提供则使用 protocol 中的

        Returns:
            TecanMCA384ScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许获取适配器

        Example:
            >>> adapter = MCA384HeadAdapter(Label="EVA[001]")
            >>> mca = protocol.mca()
            >>> mca.get_head_adapter(adapter)
        """
        # 状态验证
        self._validate_state(MCAState.IDLE, "GetHeadAdapter")
        self._validate_adapter(adapter)

        # 获取设备序列号
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            fluent_sn = "19905"  # 向后兼容的默认值

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.Mca._384.Scripting.Mca384GetHeadAdapterScriptCommandDataV1")
        get_head = SubElement(object_elem, "Mca384GetHeadAdapterScriptCommandDataV1")

        SubElement(get_head, "BlowoutAirgap").text = self.DEFAULT_POSITION

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(get_head, adapter.Label)
        self._add_common_device_data(common_data_v2, fluent_sn)

        xml_command = "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态
        self.state = MCAState.ADAPTER_LOADED
        self.current_adapter = adapter
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def get_head_adapter(self, adapter: MCA384HeadAdapter, fluent_sn: str = None):
        """
        获取头部适配器 (链式调用友好的方法名)
        
        Args:
            adapter (MCA384HeadAdapter): 适配器对象
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanMCA384ScriptGenerator: 支持链式调用
        """
        return self.GetHeadAdapter(adapter, fluent_sn)

    def DropHeadAdapter(self, fluent_sn: str = None):
        """
        释放 MCA384 头部适配器 (支持链式调用和状态管理)

        Args:
            fluent_sn (str, optional): 设备序列号，如果未提供则使用 protocol 中的

        Returns:
            TecanMCA384ScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许释放适配器

        Example:
            >>> mca = protocol.mca()
            >>> mca.drop_head_adapter()
        """
        # 状态验证 - 可以在有适配器或有枪头时释放
        if self.state not in [MCAState.ADAPTER_LOADED, MCAState.TIPS_LOADED]:
            raise InvalidStateException(
                f"错误：无法执行 DropHeadAdapter。"
                f"当前状态: {self.state.name}，要求状态: ADAPTER_LOADED 或 TIPS_LOADED"
            )

        # 获取设备序列号
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            fluent_sn = "19905"  # 向后兼容的默认值

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384DropHeadAdapterScriptCommandDataV1")
        drop_head = SubElement(object_elem, "Mca384DropHeadAdapterScriptCommandDataV1")

        SubElement(drop_head, "BlowoutAirgap").text = self.DEFAULT_POSITION

        use_source = SubElement(drop_head, "UseSourceAsBackPosition")
        SubElement(use_source, "Backs").text = "BackToSource"
        SubElement(drop_head, "AdapterAfterDrop").text = "False"

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(drop_head)
        self._add_common_device_data(common_data_v2, fluent_sn)

        xml_command = "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态
        self.state = MCAState.IDLE
        self.current_adapter = None
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def drop_head_adapter(self, fluent_sn: str = None):
        """
        释放头部适配器 (链式调用友好的方法名)
        
        Args:
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanMCA384ScriptGenerator: 支持链式调用
        """
        return self.DropHeadAdapter(fluent_sn)

    def PickUpTips(
            self,
            adapter: MCA384HeadAdapter = None,
            labwareLabel: str = "MCA96 50ul[001]",
            fluent_sn: str = None
            ):
        """
        拾取枪头 (支持链式调用和状态管理)

        Args:
            adapter (MCA384HeadAdapter, optional): 头部适配器配置，如果未提供则使用当前适配器
            labwareLabel (str): 枪头架耗材标签，默认 "MCA96 50ul[001]"
            fluent_sn (str, optional): 设备序列号，如果未提供则使用 protocol 中的

        Returns:
            TecanMCA384ScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许拾取枪头
            ValueError: 如果耗材未定义

        Example:
            >>> mca = protocol.mca()
            >>> mca.get_head_adapter(adapter)
            >>> mca.pick_up_tips("MCA96 50ul[001]")

        Notes:
            - 适配器必须已正确配置
            - 默认枪头架为 50ul 枪头
        """
        # 状态验证
        self._validate_state(MCAState.ADAPTER_LOADED, "PickUpTips")
        
        # 使用默认适配器
        if adapter is None:
            adapter = self.current_adapter
        if adapter is None:
            raise ValueError("必须提供 adapter 参数或已加载适配器")
            
        self._validate_adapter(adapter)
        self._validate_labware_exists(labwareLabel)

        # 获取设备序列号
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            fluent_sn = "19905"  # 向后兼容的默认值

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384PickUpTipsScriptCommandDataV2")
        pick_up = SubElement(object_elem, "Mca384PickUpTipsScriptCommandDataV2")

        SubElement(pick_up, "BlowoutAirgap").text = self.DEFAULT_POSITION

        # Add partial tip data
        partial_tip_data = self._add_partial_tip_data(pick_up)

        # Add well selection data
        well_data = self._add_well_selection_data(partial_tip_data, adapter)

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(well_data, labwareLabel)
        self._add_common_device_data(common_data_v2, fluent_sn)

        xml_command = "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态
        self.state = MCAState.TIPS_LOADED
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def pick_up_tips(self, tip_rack_label: str = "MCA96 50ul[001]", adapter: MCA384HeadAdapter = None, fluent_sn: str = None):
        """
        拾取枪头 (链式调用友好的方法名)
        
        Args:
            tip_rack_label (str): 枪头架标签
            adapter (MCA384HeadAdapter, optional): 适配器对象
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanMCA384ScriptGenerator: 支持链式调用
        """
        return self.PickUpTips(adapter, tip_rack_label, fluent_sn)

    def SetTipsBack(
            self,
            adapter:MCA384HeadAdapter(Label="EVA[001]"),
            fluent_sn: str = "19905"
            ) -> str:
        """
        Generate XML script for returning tips to their rack using MCA384 head.

        Args:
            adapter (MCA384HeadAdapter): The head adapter configuration containing
                name and ID attributes for tip positioning
            fluent_sn (str, optional): Device serial number used in the command.
                Defaults to "19905".

        Returns:
            str: Compact XML string prefixed with "B;" containing the tip return command

        Example:
            >>> adapter = MCA384HeadAdapter(Label="EVA[001]")
            >>> generator = TecanMCAScriptGenerator()
            >>> xml = generator.SetTipsBack(adapter, fluent_sn="19905")

        Notes:
            - This command is typically used after liquid handling operations
            - The adapter configuration must match the original pickup configuration
            - Default serial number works for most single-module systems
        """
        self._validate_adapter(adapter)

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384SetTipsBackScriptCommandDataV2")
        set_tips_back = SubElement(object_elem, "Mca384SetTipsBackScriptCommandDataV2")

        use_source = SubElement(set_tips_back, "UseSourceAsBackPosition")
        SubElement(use_source, "Backs").text = "BackToSource"

        # Add partial tip data
        partial_tip_data = self._add_partial_tip_data(set_tips_back, "0", "0")

        # Add well selection data
        well_data = self._add_well_selection_data(partial_tip_data, adapter)

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(well_data)
        self._add_common_device_data(common_data_v2, fluent_sn)

        return "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')

    def Aspirate(
            self,
            adapter: MCA384HeadAdapter(Label="EVA[001]"),
            volume: float,
            labwareLabel: str,
            liquid_class: LiquidClass.Water_Free_Single,
            fluent_sn: str = "19905"
            ) -> str:
        """
        Generate XML script for aspiration operation using MCA384 head.

        Args:
            adapter (MCA384HeadAdapter): Configured head adapter with name and ID
            volume (float): Volume to aspirate in microliters (μL)
            labwareLabel (str): Label of the source labware (e.g., "96 Well Flat[001]")
            liquid_class (str): Liquid class name for aspiration (e.g., "Water Free Single")
            fluent_sn (str, optional): Device serial number. Defaults to "19905".

        Returns:
            str: Compact XML string prefixed with "B;" containing aspiration command

        Example:
            >>> adapter =MCA384HeadAdapter(Label="EVA[001]")
            >>> MCA384 = TecanMCAScriptGenerator()
            >>> xml = MCA384.Aspirate(
            ...     adapter=adapter,
            ...     volume=100.0,
            ...     labwareLabel="96 Well Flat[001]",
            ...     liquid_class="Water Free Single",
            ...     fluent_sn="19905"
            ... )

        Raises:
            ValueError: If volume is not positive
            AttributeError: If adapter is missing required attributes

        Notes:
            - Volume precision is typically 0.1 μL
            - Liquid class determines flow rates and other aspiration parameters
            - Adapter configuration must match physical setup
        """
        self._validate_adapter(adapter)

        if isinstance(liquid_class, Enum):
            liquid_class_name = liquid_class.value
        else:
            raise ValueError(f"Invalid liquid_class,{liquid_class} ")

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Commands.Mca384.Mca384AspirateScriptCommandDataV2")
        aspirate = SubElement(object_elem, "Mca384AspirateScriptCommandDataV2")

        # Add pipetting data
        pipetting = SubElement(aspirate, "Data",
                               Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384PipettingWithVolumesScriptCommandDataV2")
        pipetting_data = SubElement(pipetting, "Mca384PipettingWithVolumesScriptCommandDataV2")

        self._add_pipetting_params(pipetting_data, volume, liquid_class_name)

        # Add well selection data
        well_data = self._add_well_selection_data(pipetting_data, adapter)

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(well_data, labwareLabel)
        self._add_common_device_data(common_data_v2, fluent_sn)

        return "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')

    def Dispense(
            self,
            adapter: MCA384HeadAdapter(Label="EVA[001]"),
            volume: float,
            labwareLabel: str,
            liquid_class: LiquidClass.Water_Free_Single,
            fluent_sn: str = "19905"
            ) -> str:
        """
        Generate XML script for aspiration operation using MCA384 head.

        Args:
            adapter (MCA384HeadAdapter): Configured head adapter with name and ID
            volume (float): Volume to aspirate in microliters (μL)
            labwareLabel (str): Label of the source labware (e.g., "96 Well Flat[001]")
            liquid_class (str): Liquid class name for aspiration (e.g., "Water Free Single")
            fluent_sn (str, optional): Device serial number. Defaults to "19905".

        Returns:
            str: Compact XML string prefixed with "B;" containing aspiration command

        Example:
            >>> adapter =MCA384HeadAdapter(Label="EVA[001]")
            >>> MCA384 = TecanMCAScriptGenerator()
            >>> xml = MCA384.Dispense(
            ...     adapter=adapter,
            ...     volume=100.0,
            ...     labwareLabel="96 Well Flat[001]",
            ...     liquid_class="Water Free Single",
            ...     fluent_sn="19905"
            ... )

        Raises:
            ValueError: If volume is not positive
            AttributeError: If adapter is missing required attributes

        Notes:
            - Volume precision is typically 0.1 μL
            - Liquid class determines flow rates and other aspiration parameters
            - Adapter configuration must match physical setup
        """
        self._validate_adapter(adapter)
        if isinstance(liquid_class, Enum):
            liquid_class_name = liquid_class.value
        else:
            raise ValueError(f"Invalid liquid_class,{liquid_class} ")
        if not isinstance(volume, (int, float)) or volume <= 0:
            raise ValueError("Volume must be a positive number")

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Commands.Mca384.Mca384DispenseScriptCommandDataV2")
        dispense = SubElement(object_elem, "Mca384DispenseScriptCommandDataV2")

        # Add pipetting data
        pipetting = SubElement(dispense, "Data",
                               Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384PipettingWithVolumesScriptCommandDataV2")
        pipetting_data = SubElement(pipetting, "Mca384PipettingWithVolumesScriptCommandDataV2")

        self._add_pipetting_params(pipetting_data, volume, liquid_class_name)

        # Add well selection data
        well_data = self._add_well_selection_data(pipetting_data, adapter)

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(well_data, labwareLabel)
        self._add_common_device_data(common_data_v2, fluent_sn)

        return "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')

    def Mix(self,
            adapter: MCA384HeadAdapter(Label="EVA[001]"),
            volume:float,
            labwareLabel: str,
            liquid_class: LiquidClass.Water_Mix,
            cycles:int,
            fluent_sn="19905")->str:
        """Generate XML script for mixing operation.

        Args:
            adapter (MCA384HeadAdapter): The adapter plate object
            volume (float): Mixing volume in µl
            labware (str): Labware name (e.g., "96 Well Flat[001]")
            liquid_class (str): Liquid class name (e.g., "Water Mix")
            cycles (int): Number of mixing cycles
            fluent_sn (str): Fluent serial number (default "19905")

        Returns:
            str: XML script string with "B;" prefix
        """
        self._validate_adapter(adapter)
        if isinstance(liquid_class, Enum):
            liquid_class_name = liquid_class.value
        else:
            raise ValueError(f"Invalid liquid_class,{liquid_class} ")
        if not isinstance(volume, (int, float)) or volume <= 0:
            raise ValueError("Volume must be a positive number")
        if not isinstance(cycles, int) or cycles <= 0:
            raise ValueError("Cycles must be a positive integer")

        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Scripting.Commands.Mca384.Mca384MixScriptCommandDataV2")
        mix = SubElement(object_elem, "Mca384MixScriptCommandDataV2")

        # Add cycles parameter
        SubElement(mix, "Cycles").text = str(cycles)

        # Add pipetting data
        pipetting = SubElement(mix, "Data",
                               Type="Tecan.Core.Instrument.Devices.Mca.Mca384.Scripting.Mca384PipettingWithVolumesScriptCommandDataV2")
        pipetting_data = SubElement(pipetting, "Mca384PipettingWithVolumesScriptCommandDataV2")

        self._add_pipetting_params(pipetting_data, volume, liquid_class_name)

        # Add well selection data
        well_data = self._add_well_selection_data(pipetting_data, adapter)

        # Add common data structure
        common_data_v2 = self._add_common_data_v2(well_data, labwareLabel)
        self._add_common_device_data(common_data_v2, fluent_sn)

        return "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')