from xml.etree.ElementTree import Element, SubElement, tostring
from xml.sax.saxutils import escape
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Protocol import Protocol, RGAState, InvalidStateException
else:
    try:
        from Protocol import RGAState, InvalidStateException
    except ImportError:
        # 为了向后兼容，如果没有 Protocol 模块，定义简单的状态类
        from enum import Enum, auto
        class RGAState(Enum):
            IDLE = auto()
            HOLDING = auto()
        class InvalidStateException(Exception):
            pass


class TecanRGAScriptGenerator:
    def __init__(self, protocol: Optional['Protocol'] = None):
        """
        初始化 RGA 指令生成器
        
        Args:
            protocol (Protocol, optional): 协议实例，用于链式调用和状态管理
        """
        self.protocol = protocol
        
        # 状态管理
        self.state = RGAState.IDLE
        self.current_labware: Optional[str] = None
    
    def _validate_state(self, required_state: RGAState, operation_name: str) -> None:
        """
        验证当前状态是否允许执行指定操作
        
        Args:
            required_state (RGAState): 要求的状态
            operation_name (str): 操作名称，用于错误信息
            
        Raises:
            InvalidStateException: 当状态不匹配时
        """
        if self.state != required_state:
            raise InvalidStateException(
                f"错误：无法执行 {operation_name}。"
                f"当前状态: {self.state.name}，要求状态: {required_state.name}"
            )
    
    def _execute_command(self, xml_command: str) -> 'TecanRGAScriptGenerator':
        """
        执行命令：将 XML 添加到协议或返回字符串
        
        Args:
            xml_command (str): 生成的 XML 指令
            
        Returns:
            TecanRGAScriptGenerator: 返回自身支持链式调用，或字符串（向后兼容）
        """
        if self.protocol:
            self.protocol.add_command(xml_command)
            return self
        else:
            # 向后兼容：直接返回 XML 字符串
            return xml_command

    def TransferLabware(self, Labware, TargetLocation, TargetPosition, OnlyUseSelectedSite=True):
        # 创建根元素
        script_group = Element("ScriptGroup")

        # 创建Objects元素
        objects = SubElement(script_group, "Objects")

        # 创建Object元素
        object_elem = SubElement(objects, "Object",
                                 Type="Tecan.VisionX.ApplicationDriver.ApplicationDriverBase.ApplicationDriverMacro")

        # 创建ApplicationDriverMacro元素
        macro = SubElement(object_elem, "ApplicationDriverMacro",
                           Version="1",
                           Name="RGA1_TransferLabware",
                           ModuleName="RGA 1",
                           ExecutionTime="PT0S",
                           IsBreakpoint="false",
                           IsDisabledForExecution="false",
                           LineNumber="1")

        # 创建ExecutionSettings内容
        params = f"""
        <TransferLabwareCommandParameters xmlns:i="http://www.w3.org/2001/XMLSchema-instance" 
                                         xmlns="http://schemas.datacontract.org/2004/07/Tecan.VisionX.Drivers.RobotDriverBase">
            <FixedSite>{str(OnlyUseSelectedSite).lower()}</FixedSite>
            <Labware>{Labware}</Labware>
            <Location>{TargetLocation}</Location>
            <MoveToBase>false</MoveToBase>
            <OnTheFlyTool></OnTheFlyTool>
            <Site>{TargetPosition}</Site>
            <UseOnTheFlyTool>false</UseOnTheFlyTool>
        </TransferLabwareCommandParameters>
        """
        # 压缩并转义XML
        compressed_params = ' '.join(params.split())
        SubElement(macro, "ExecutionSettings").text = escape(compressed_params)

        # 添加ScriptGroup的其他元素
        SubElement(script_group, "Name")
        SubElement(script_group, "IsBreakpoint").text = "False"
        SubElement(script_group, "IsDisabledForExecution").text = "False"
        SubElement(script_group, "LineNumber").text = "0"

        # 转换为紧凑格式的XML字符串
        xml_command = "B;" + tostring(script_group, encoding='utf-8').decode('utf-8')
        
        # 更新状态（简化的状态管理，实际应用中可能更复杂）
        if self.state == RGAState.IDLE:
            self.state = RGAState.HOLDING
            self.current_labware = Labware
        else:
            # 如果已经在抓取状态，这可能是放置操作
            self.state = RGAState.IDLE
            self.current_labware = None
        
        return self._execute_command(xml_command)
    
    # 链式调用友好的方法
    def transfer_labware(self, labware: str, target_location: str, target_position: int, 
                        only_use_selected_site: bool = True):
        """
        转移耗材 (链式调用友好的方法名)
        
        Args:
            labware (str): 耗材名称
            target_location (str): 目标位置
            target_position (int): 目标位置编号
            only_use_selected_site (bool): 是否只使用选定位点
            
        Returns:
            TecanRGAScriptGenerator: 支持链式调用
        """
        return self.TransferLabware(labware, target_location, target_position, only_use_selected_site)