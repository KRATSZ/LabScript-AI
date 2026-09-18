from xml.etree.ElementTree import Element, SubElement, tostring
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Protocol import Protocol, FCAState, InvalidStateException
else:
    try:
        from Protocol import FCAState, InvalidStateException
    except ImportError:
        # 为了向后兼容，如果没有 Protocol 模块，定义简单的状态类
        from enum import Enum, auto
        class FCAState(Enum):
            IDLE = auto()
            TIPS_LOADED = auto()
        class InvalidStateException(Exception):
            pass


class TecanFCAScriptGenerator:
    def __init__(self, protocol: Optional['Protocol'] = None):
        """
        初始化 FCA 指令生成器
        
        Args:
            protocol (Protocol, optional): 协议实例，用于链式调用和状态管理
        """
        self.protocol = protocol
        
        # XML 生成常量
        self.DEVICE_ALIAS = "Instrument=1/Device=LIHA:1"
        self.DEFAULT_BOOL = "False"
        self.DEFAULT_LINE_NUMBER = "1"
        self.SCRIPT_GROUP_LINE_NUMBER = "0"
        self.PREFIX = "B;"
        self.DEFAULT_OFFSET = "0"
        self.TIP_SPACING = "9"
        self.COMPARTMENT = "1"
        
        # 状态管理
        self.state = FCAState.IDLE
        self.current_tip_type: Optional[str] = None
        self.current_channels: Optional[List[int]] = None
    
    def _validate_state(self, required_state: FCAState, operation_name: str) -> None:
        """
        验证当前状态是否允许执行指定操作
        
        Args:
            required_state (FCAState): 要求的状态
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
    
    def _execute_command(self, xml_command: str) -> 'TecanFCAScriptGenerator':
        """
        执行命令：将 XML 添加到协议或返回字符串
        
        Args:
            xml_command (str): 生成的 XML 指令
            
        Returns:
            TecanFCAScriptGenerator: 返回自身支持链式调用，或字符串（向后兼容）
        """
        if self.protocol:
            self.protocol.add_command(xml_command)
            return self
        else:
            # 向后兼容：直接返回 XML 字符串
            # 注意：这种情况下无法链式调用
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

    def _add_common_device_data(self, parent, fluent_sn):
        """Add common device alias and ID information."""
        device_alias_data = SubElement(parent, "Data",
                                       Type="Tecan.Core.Instrument.Helpers.Scripting.DeviceAliasStatementBaseDataV1")
        device_alias = SubElement(device_alias_data, "DeviceAliasStatementBaseDataV1")

        SubElement(device_alias, "Alias", Type="Tecan.Core.Instrument.DeviceAlias.DeviceAlias").text = self.DEVICE_ALIAS

        id_elem = SubElement(device_alias, "ID")
        SubElement(id_elem, "AvailableID").text = f"USB:TECAN,MYRIUS,{fluent_sn}/LIHA:1"

        self._add_script_statement(device_alias)

    def _add_script_statement(self, parent):
        """Add common script statement data."""
        script_data = SubElement(parent, "Data",
                                 Type="Tecan.Core.Scripting.Helpers.ScriptStatementBaseDataV1")
        script_base = SubElement(script_data, "ScriptStatementBaseDataV1")

        SubElement(script_base, "IsBreakpoint").text = self.DEFAULT_BOOL
        SubElement(script_base, "IsDisabledForExecution").text = self.DEFAULT_BOOL
        SubElement(script_base, "GroupLineNumber").text = self.DEFAULT_OFFSET
        SubElement(script_base, "LineNumber").text = self.DEFAULT_LINE_NUMBER

    def _add_common_data_v2(self, parent, labware_name=""):
        """Add common ScriptCommandCommonDataV2 structure."""
        common_data = SubElement(parent, "Data",
                                 Type="Tecan.Core.Instrument.Helpers.Scripting.ScriptCommandCommonDataV2")
        common_data_v2 = SubElement(common_data, "ScriptCommandCommonDataV2")

        SubElement(common_data_v2, "LabwareName").text = labware_name
        SubElement(common_data_v2, "LiquidClassVariablesNames")
        SubElement(common_data_v2, "LiquidClassVariablesValues")

        return common_data_v2

    def _add_tip_selection(self, parent, use_channels):
        """Add tip selection structure."""
        SubElement(parent, "SerializedTipsIndexes")

        selected_tips = SubElement(parent, "SelectedTipsIndexes")
        for channel in use_channels:
            obj = SubElement(selected_tips, "Object", Type="System.Int32")
            SubElement(obj, "int").text = str(channel)

        SubElement(parent, "TipMask")
        SubElement(parent, "TipOffset").text = self.DEFAULT_OFFSET
        SubElement(parent, "TipSpacing").text = self.TIP_SPACING

    def _add_well_selection(self, parent, selected_well):
        """Add well selection structure."""
        serialized_indexes = self.wells_string_to_indexes(selected_well)
        SubElement(parent, "SerializedWellIndexes").text = serialized_indexes
        SubElement(parent, "SelectedWellsString").text = selected_well
        SubElement(parent, "WellOffset").text = self.DEFAULT_OFFSET

    def _add_pipetting_data(self, parent, volumes, liquid_class):
        """Add pipetting data structure."""
        # Add volumes
        volumes_elem = SubElement(parent, "Volumes")
        for vol in volumes:
            obj = SubElement(volumes_elem, "Object", Type="System.String")
            SubElement(obj, "string").text = str(vol)

        # Add liquid class parameters
        SubElement(parent, "FlowRates")
        SubElement(parent, "IsLiquidClassNameByExpressionEnabled").text = self.DEFAULT_BOOL

        liquid_class_mode = SubElement(parent, "LiquidClassSelectionMode")
        SubElement(liquid_class_mode, "LiquidClassSelectionMode").text = "SingleByName"

        SubElement(parent, "LiquidClassNameBySelection").text = liquid_class
        SubElement(parent, "LiquidClassNameByExpression")

        # Add empty LiquidClassNames (8 items)
        liquid_class_names = SubElement(parent, "LiquidClassNames")
        for _ in range(8):
            obj = SubElement(liquid_class_names, "Object", Type="System.String")
            SubElement(obj, "string")

        SubElement(parent, "Compartment").text = self.COMPARTMENT

    def GetTips(self, tip_type, use_channels, fluent_sn=None):
        """
        获取枪头 (支持链式调用和状态管理)
        
        Args:
            tip_type (str): 枪头类型 (如 "1000ul")
            use_channels (List[int]): 使用的通道列表
            fluent_sn (str, optional): 设备序列号，如果未提供则使用 protocol 中的
            
        Returns:
            TecanFCAScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许获取枪头
        """
        # 状态验证
        self._validate_state(FCAState.IDLE, "GetTips")
        
        # 获取设备序列号
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            raise ValueError("必须提供 fluent_sn 参数或在 Protocol 中设置")
            
        # 生成 XML
        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaGetTipsScriptCommandDataV3")
        liha_get_tips = SubElement(object_elem, "LihaGetTipsScriptCommandDataV3")

        # Add tip selection data
        data_v1 = SubElement(liha_get_tips, "Data",
                             Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LiHaScriptCommandUsingTipSelectionBaseDataV1")
        liha_base = SubElement(data_v1, "LiHaScriptCommandUsingTipSelectionBaseDataV1")
        self._add_tip_selection(liha_base, use_channels)

        # Add common device data
        data_v2 = SubElement(liha_base, "Data",
                             Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaScriptCommandDataV1")
        liha_cmd = SubElement(data_v2, "LihaScriptCommandDataV1")
        common_data_v2 = self._add_common_data_v2(liha_cmd)
        self._add_common_device_data(common_data_v2, fluent_sn)

        # Add other parameters
        SubElement(liha_get_tips, "AirgapVolume").text = "10"
        SubElement(liha_get_tips, "AirgapSpeed").text = "70"

        diti_type = SubElement(liha_get_tips, "DitiType")
        SubElement(diti_type, "AvailableID").text = f"TOOLTYPE:LiHa.TecanDiTi/TOOLNAME:FCA, {tip_type}"

        SubElement(liha_get_tips, "UseNextPosition").text = "True"

        xml_command = self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态
        self.state = FCAState.TIPS_LOADED
        self.current_tip_type = tip_type
        self.current_channels = list(use_channels)
        
        return self._execute_command(xml_command)
    
    # 添加链式调用的友好方法
    def get_tips(self, tip_type, channels, fluent_sn=None):
        """
        获取枪头 (链式调用友好的方法名)
        
        Args:
            tip_type (str): 枪头类型 (如 "1000ul") 
            channels (List[int]): 使用的通道列表
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator: 支持链式调用
        """
        return self.GetTips(tip_type, channels, fluent_sn)

    def _create_pipetting_command(self, command_type, volumes, labware_name, use_channels,
                                  liquid_class, selected_well, fluent_sn, additional_params=None):
        """Generic method to create pipetting commands (Aspirate/Dispense/Mix)."""
        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object", Type=command_type)
        command = SubElement(object_elem, command_type.split('.')[-1])

        # Add basic parameters
        if additional_params:
            for param, value in additional_params.items():
                SubElement(command, param).text = str(value)

        # Add pipetting data
        pipetting = SubElement(command, "Data",
                               Type="Tecan.Core.Instrument.Devices.Scripting.Data.LihaPipettingWithVolumesScriptCommandDataV7")
        pipetting_data = SubElement(pipetting, "LihaPipettingWithVolumesScriptCommandDataV7")
        self._add_pipetting_data(pipetting_data, volumes, liquid_class)

        # Add well selection
        well_selection = SubElement(pipetting_data, "Data",
                                    Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaScriptCommandUsingWellSelectionBaseDataV1")
        well_data = SubElement(well_selection, "LihaScriptCommandUsingWellSelectionBaseDataV1")
        self._add_well_selection(well_data, selected_well)

        # Add tip selection
        tip_selection = SubElement(well_data, "Data",
                                   Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LiHaScriptCommandUsingTipSelectionBaseDataV1")
        tip_data = SubElement(tip_selection, "LiHaScriptCommandUsingTipSelectionBaseDataV1")
        self._add_tip_selection(tip_data, use_channels)

        # Add common device data
        liha_cmd = SubElement(tip_data, "Data",
                              Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaScriptCommandDataV1")
        liha_cmd_data = SubElement(liha_cmd, "LihaScriptCommandDataV1")
        common_data_v2 = self._add_common_data_v2(liha_cmd_data, labware_name)
        self._add_common_device_data(common_data_v2, fluent_sn)

        return self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')

    def Aspirate(self, volume, labwarelabel, use_channels=None, liquid_class=None, selected_well=None, fluent_sn=None):
        """
        吸液操作 (支持链式调用和状态管理)
        
        Args:
            volume (List[float] 或 float): 吸液体积列表或单一体积
            labwarelabel (str): 耗材标签
            use_channels (List[int], optional): 使用的通道，默认使用当前加载的通道
            liquid_class (str, optional): 液体类型
            selected_well (str, optional): 选择的孔位
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许吸液
            ValueError: 如果耗材未定义
        """
        # 状态验证
        self._validate_state(FCAState.TIPS_LOADED, "Aspirate")
        
        # 验证耗材存在
        self._validate_labware_exists(labwarelabel)
        
        # 使用默认参数
        if use_channels is None:
            use_channels = self.current_channels
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            raise ValueError("必须提供 fluent_sn 参数或在 Protocol 中设置")
            
        # 如果传入单一体积，转换为列表
        if isinstance(volume, (int, float)):
            volume = [volume] * len(use_channels)
            
        xml_command = self._create_pipetting_command(
            command_type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaAspirateScriptCommandDataV5",
            volumes=volume,
            labware_name=labwarelabel,
            use_channels=use_channels,
            liquid_class=liquid_class,
            selected_well=selected_well,
            fluent_sn=fluent_sn,
            additional_params={
                "IsSwitchContainerSourceEnabled": "False",
                "OffsetX": self.DEFAULT_OFFSET,
                "OffsetY": self.DEFAULT_OFFSET
            }
        )
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def aspirate(self, volume, labware, wells=None, liquid_class="Water Free Single", channels=None, fluent_sn=None):
        """
        吸液操作 (链式调用友好的方法名)
        
        Args:
            volume (List[float] 或 float): 吸液体积
            labware (str): 耗材标签
            wells (str, optional): 孔位字符串 (如 "A1,B1,C1")
            liquid_class (str): 液体类型，默认 "Water Free Single"
            channels (List[int], optional): 通道列表
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator: 支持链式调用
        """
        return self.Aspirate(volume, labware, channels, liquid_class, wells, fluent_sn)

    def Dispense(self, volume, labwarelabel, use_channels=None, liquid_class=None, selected_well=None, fluent_sn=None):
        """
        排液操作 (支持链式调用和状态管理)
        
        Args:
            volume (List[float] 或 float): 排液体积列表或单一体积
            labwarelabel (str): 耗材标签
            use_channels (List[int], optional): 使用的通道，默认使用当前加载的通道
            liquid_class (str, optional): 液体类型
            selected_well (str, optional): 选择的孔位
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许排液
            ValueError: 如果耗材未定义
        """
        # 状态验证
        self._validate_state(FCAState.TIPS_LOADED, "Dispense")
        
        # 验证耗材存在
        self._validate_labware_exists(labwarelabel)
        
        # 使用默认参数
        if use_channels is None:
            use_channels = self.current_channels
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            raise ValueError("必须提供 fluent_sn 参数或在 Protocol 中设置")
            
        # 如果传入单一体积，转换为列表
        if isinstance(volume, (int, float)):
            volume = [volume] * len(use_channels)
            
        xml_command = self._create_pipetting_command(
            command_type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaDispenseScriptCommandDataV6",
            volumes=volume,
            labware_name=labwarelabel,
            use_channels=use_channels,
            liquid_class=liquid_class,
            selected_well=selected_well,
            fluent_sn=fluent_sn,
            additional_params={
                "OffsetX": self.DEFAULT_OFFSET,
                "OffsetY": self.DEFAULT_OFFSET,
                "SkipZOnlyMoveToPipettingPosition": "False",
                "DispenseDelays": ""
            }
        )
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def dispense(self, volume, labware, wells=None, liquid_class="Water Free Single", channels=None, fluent_sn=None):
        """
        排液操作 (链式调用友好的方法名)
        
        Args:
            volume (List[float] 或 float): 排液体积
            labware (str): 耗材标签
            wells (str, optional): 孔位字符串 (如 "A1,B1,C1")
            liquid_class (str): 液体类型，默认 "Water Free Single"
            channels (List[int], optional): 通道列表
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator: 支持链式调用
        """
        return self.Dispense(volume, labware, channels, liquid_class, wells, fluent_sn)

    def Mix(self, cycles, volume, labwarelabel, use_channels, liquid_class, selected_well, fluent_sn):
        """Generate XML script for mixing."""
        return self._create_pipetting_command(
            command_type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaMixScriptCommandDataV4",
            volumes=volume,
            labware_name=labwarelabel,
            use_channels=use_channels,
            liquid_class=liquid_class,
            selected_well=selected_well,
            fluent_sn=fluent_sn,
            additional_params={
                "Cycles": cycles,
                "OffsetX": self.DEFAULT_OFFSET,
                "OffsetY": self.DEFAULT_OFFSET
            }
        )

    def DropTips(self, use_channels=None, fluent_sn=None):
        """
        丢弃枪头 (支持链式调用和状态管理)
        
        Args:
            use_channels (List[int], optional): 使用的通道，默认使用当前加载的通道
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator 或 str: 支持链式调用或返回 XML 字符串
            
        Raises:
            InvalidStateException: 如果当前状态不允许丢弃枪头
        """
        # 状态验证
        self._validate_state(FCAState.TIPS_LOADED, "DropTips")
        
        # 使用默认参数
        if use_channels is None:
            use_channels = self.current_channels
        if fluent_sn is None and self.protocol:
            fluent_sn = self.protocol.fluent_sn
        elif fluent_sn is None:
            raise ValueError("必须提供 fluent_sn 参数或在 Protocol 中设置")
            
        # 生成 XML
        script_group, objects = self._create_base_structure()

        # Create command object
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.Core.Instrument.Devices.Scripting.Data.LihaDropTipsScriptCommandDataV2")
        drop_tips = SubElement(object_elem, "LihaDropTipsScriptCommandDataV2")

        SubElement(drop_tips, "SkipIfNothingMounted").text = self.DEFAULT_BOOL

        # Add tip selection data
        data_v1 = SubElement(drop_tips, "Data",
                             Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LiHaScriptCommandUsingTipSelectionBaseDataV1")
        liha_base = SubElement(data_v1, "LiHaScriptCommandUsingTipSelectionBaseDataV1")
        self._add_tip_selection(liha_base, use_channels)

        # Add common device data
        data_v2 = SubElement(liha_base, "Data",
                             Type="Tecan.Core.Instrument.Devices.LiHa.Scripting.LihaScriptCommandDataV1")
        liha_cmd = SubElement(data_v2, "LihaScriptCommandDataV1")
        common_data_v2 = self._add_common_data_v2(liha_cmd, "FCA Thru Deck Waste Chute_1")
        self._add_common_device_data(common_data_v2, fluent_sn)

        xml_command = self.PREFIX + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态
        self.state = FCAState.IDLE
        self.current_tip_type = None
        self.current_channels = None
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def drop_tips(self, channels=None, fluent_sn=None):
        """
        丢弃枪头 (链式调用友好的方法名)
        
        Args:
            channels (List[int], optional): 通道列表
            fluent_sn (str, optional): 设备序列号
            
        Returns:
            TecanFCAScriptGenerator: 支持链式调用
        """
        return self.DropTips(channels, fluent_sn)

    def wells_string_to_indexes(self, wells_string):
        """Convert wells string like 'A1, B2, C3' to index string like '10;11;19;20;28;29;37;45;'"""
        indexes = []
        for well in wells_string.split(','):
            well = well.strip()
            if not well: continue
            row = well[0].upper()  # A, B, C etc.
            col = int(well[1:])  # 1, 2, 3 etc.
            index = (col - 1) * 8 + (ord(row) - ord('A'))
            indexes.append(str(index))
        return ';'.join(indexes) + ';'