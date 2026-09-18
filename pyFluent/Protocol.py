"""
Protocol.py - pyFluent 核心协议类

这个模块实现了 Fluent Interface 设计模式，允许用户通过链式调用来编排实验流程。
同时提供状态管理和安全性保障，防止逻辑错误。

作者: Gaoyuan
版本: 2.0.0
"""

from typing import Set, List, Optional
from enum import Enum, auto


# ================================
# 状态管理和异常定义
# ================================

class InvalidStateException(Exception):
    """当设备状态不允许执行某操作时抛出的异常"""
    pass


class FCAState(Enum):
    """FCA (灵活通道臂) 的状态枚举"""
    IDLE = auto()          # 空闲，无枪头
    TIPS_LOADED = auto()   # 已加载枪头


class MCAState(Enum):
    """MCA (多通道臂) 的状态枚举"""
    IDLE = auto()                # 空闲，无适配器
    ADAPTER_LOADED = auto()      # 已加载适配器，无枪头
    TIPS_LOADED = auto()         # 已加载适配器和枪头


class RGAState(Enum):
    """RGA (机械臂) 的状态枚举"""
    IDLE = auto()          # 空闲，无抓取物品
    HOLDING = auto()       # 正在抓取板子


# ================================
# 核心 Protocol 类
# ================================

class Protocol:
    """
    pyFluent 协议编排器，实现 Fluent Interface 设计模式
    
    使用示例:
        protocol = Protocol(fluent_sn="19905", output_file="my_protocol.gwl")
        
        protocol.add_labware(LabwareType.WELL_96_FLAT, "SourcePlate[001]", position=1) \\
                .add_labware(LabwareType.WELL_96_FLAT, "DestPlate[001]", position=2)
        
        fca = protocol.fca()
        fca.get_tips("1000ul", channels=[0,1,2,3]) \\
           .aspirate(100, "SourcePlate[001]", wells="A1,B1,C1,D1") \\
           .dispense(100, "DestPlate[001]", wells="A1,B1,C1,D1") \\
           .drop_tips()
        
        protocol.save()
    """
    
    def __init__(self, fluent_sn: str, output_file: str):
        """
        初始化协议编排器
        
        Args:
            fluent_sn (str): Tecan Fluent 设备序列号
            output_file (str): 输出的 .gwl 文件路径
        """
        self.fluent_sn = fluent_sn
        self.output_file = output_file
        self._commands: List[str] = []
        self._defined_labware: Set[str] = set()  # 用于后续验证
        
        # 实例化所有硬件臂的控制器 (延迟导入避免循环依赖)
        self._fca_gen = None
        self._mca_gen = None
        self._worktable_gen = None
        self._rga_gen = None
    
    def add_command(self, command: str) -> None:
        """
        内部方法，供各个生成器回调，用以添加指令
        
        Args:
            command (str): 要添加的 XML 指令字符串
        """
        self._commands.append(command)
    
    def get_defined_labware(self) -> Set[str]:
        """
        获取已定义的耗材标签集合
        
        Returns:
            Set[str]: 已定义的耗材标签
        """
        return self._defined_labware.copy()
    
    def fca(self):
        """
        获取 FCA (灵活通道臂) 控制器
        
        Returns:
            TecanFCAScriptGenerator: FCA 控制器实例
        """
        if self._fca_gen is None:
            from FCACommand import TecanFCAScriptGenerator
            self._fca_gen = TecanFCAScriptGenerator(protocol=self)
        return self._fca_gen
    
    def mca(self):
        """
        获取 MCA (多通道臂) 控制器
        
        Returns:
            TecanMCA384ScriptGenerator: MCA 控制器实例
        """
        if self._mca_gen is None:
            from MCA384Commond import TecanMCA384ScriptGenerator
            self._mca_gen = TecanMCA384ScriptGenerator(protocol=self)
        return self._mca_gen
    
    def worktable(self):
        """
        获取工作台控制器
        
        Returns:
            TecanWorktableScriptGenerator: 工作台控制器实例
        """
        if self._worktable_gen is None:
            from WortableCommand import TecanWorktableScriptGenerator
            self._worktable_gen = TecanWorktableScriptGenerator(protocol=self)
        return self._worktable_gen
    
    def rga(self):
        """
        获取 RGA (机械臂) 控制器
        
        Returns:
            TecanRGAScriptGenerator: RGA 控制器实例
        """
        if self._rga_gen is None:
            from RGACommond import TecanRGAScriptGenerator
            self._rga_gen = TecanRGAScriptGenerator(protocol=self)
        return self._rga_gen
    
    def add_labware(self, labware_type, labware_label: str, location, position: int, 
                   rotation: int = 0, has_lid: bool = False) -> 'Protocol':
        """
        添加耗材到工作台 (便捷方法)
        
        Args:
            labware_type: 耗材类型 (来自 FluentLabware.LabwareType)
            labware_label (str): 耗材标签
            location: 位置 (来自 FluentLabware.Nest_position)
            position (int): 位置编号
            rotation (int): 旋转角度，默认 0
            has_lid (bool): 是否有盖子，默认 False
            
        Returns:
            Protocol: 返回自身，支持链式调用
        """
        command = self.worktable().AddLabware(
            LabwareType=labware_type,
            LabwareLabel=labware_label,
            Location=location,
            Position=position,
            Rotation=rotation,
            HasLid=has_lid
        )
        # 注意：AddLabware 已经通过回调添加了指令，这里我们只需要记录标签
        self._defined_labware.add(labware_label)
        return self
    
    def save(self) -> None:
        """
        将所有累积的指令写入 .gwl 文件
        """
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for command in self._commands:
                f.write(command + "\n")
        print(f"脚本已成功生成到: {self.output_file}")
    
    def get_command_count(self) -> int:
        """
        获取当前累积的指令数量
        
        Returns:
            int: 指令数量
        """
        return len(self._commands)
    
    def clear_commands(self) -> None:
        """
        清空所有指令 (用于调试或重新开始)
        """
        self._commands.clear()
        self._defined_labware.clear()
        print("所有指令和耗材记录已清空")