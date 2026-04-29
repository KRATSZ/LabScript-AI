import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.hamilton.vantage_tests import VantageCommandCatcher
from pylabrobot.resources.hamilton import (
    VantageDeck,
    TIP_CAR_480_A00,
    PLT_CAR_L5AC_A00,
)
from pylabrobot.resources import STF, Cor_96_wellplate_360ul_Fb
from pylabrobot.resources.coordinate import Coordinate

async def main():
  """
  用 PyLabRobot 控制 Hamilton Vantage。
  """
  # 1. 初始化后端和工作台
  backend = VantageBackend()
  #用模拟器的话：backend = VantageCommandCatcher()
  deck = VantageDeck(size=1.3)
  lh = LiquidHandler(backend=backend, deck=deck)

  # 2. 定义并放置资源
  # 定义吸头载架 (rails=19) 和吸头架 (STF, 300uL)
  tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
  deck.assign_child_resource(tip_carrier, rails=19)
  tip_rack = STF(name="tip_rack_1")
  tip_carrier[0] = tip_rack

  # 定义孔板载架 (rails=11)，放置两个酶标板
  plate_carrier = PLT_CAR_L5AC_A00(name="plate_carrier")
  deck.assign_child_resource(plate_carrier, rails=11)

  # 白色板子（原储液槽位置）放在 site 4 (索引3) - 作为液体来源
  source_plate = Cor_96_wellplate_360ul_Fb(name="source_plate")
  plate_carrier[3] = source_plate

  # 目标酶标板放在 site 5 (索引4)
  target_plate = Cor_96_wellplate_360ul_Fb(name="target_plate")
  plate_carrier[4] = target_plate

  try:
    # 3. 连接并初始化机器人
    print("正在设置并初始化 Vantage...")
    await lh.setup()
    print("初始化完成。")

    # 4. 执行梯度稀释操作
    print("开始执行梯度稀释...")

    # 4.1. 添加 PBS 到目标板 (A2-A12)
    print("步骤 1: 添加 100uL PBS 到目标板的 A2-A12 孔...")
    # "rows[0]" 代表第一行的所有8个吸头
    await lh.pick_up_tips(tip_rack.rows[0])
    for i in range(2, 13):
      well_name = f"A{i}"
      print(f"  - 向 {well_name} 中添加 PBS")
      # 从 source_plate 的第一列（所有8个孔）吸取液体
      await lh.aspirate(source_plate.columns[0], vols=[100]*8)
      # 循环地将液体分配到 target_plate 的第 2 到 12 列
      for i in range(1, 12): # 列的索引是从 0 开始的
          await lh.dispense(target_plate.columns[i], vols=[100]*8)
    await lh.drop_tips(tip_rack["A1"])
    print("PBS 添加完毕。")

    # 4.2. 执行系列稀释
    print("\n步骤 2: 执行系列稀释 (A1 -> A2 -> ... -> A11)...")
    await lh.pick_up_tips(tip_rack["B1"]) # 使用新吸头

    # 初始转移
    print("  - 从 A1 转移 100uL 到 A2")
    await lh.aspirate(target_plate["A1"], vols=[100])
    await lh.dispense(target_plate["A2"], vols=[100])

    # 循环稀释与混匀
    for i in range(2, 11):
      source_well_name = f"A{i}"
      dest_well_name = f"A{i+1}"
      print(f"  - 在 {source_well_name} 中混匀, 然后转移到 {dest_well_name}")
      # 混匀 (通过重复吸取和分配实现)
      for _ in range(3):
          await lh.aspirate(target_plate[source_well_name], vols=[150])
          await lh.dispense(target_plate[source_well_name], vols=[150])
      # 转移
      await lh.aspirate(target_plate[source_well_name], vols=[100])
      await lh.dispense(target_plate[dest_well_name], vols=[100])

    # 最后一孔混匀
    print("  - 在 A11 中进行最终混匀")
    for _ in range(3):
        await lh.aspirate(target_plate["A11"], vols=[150])
        await lh.dispense(target_plate["A11"], vols=[150])

    # 丢弃吸头
    await lh.drop_tips(tip_rack["B1"])
    print("系列稀释完成。")

    print("\n演示脚本执行完毕。")

  except Exception as e:
    print(f"执行过程中发生错误: {e}")
    print(f"错误类型: {type(e).__name__}")
    if hasattr(e, 'raw_response'):
      print(f"原始响应: {e.raw_response}")
    # 提供一些故障排除建议
    if "Wrong tip detected" in str(e):
      print("\n[!] 故障排除建议: 'Wrong tip detected'")
      print("- 最常见的原因是代码中的吸头类型与物理吸头不符。")
      print("- 当前代码使用的是 'STF' (300uL 带过滤芯吸头)。")
      print("- 请检查物理吸头是否为其他类型, 如 'HTF' (1000uL 带过滤芯) 或 'LTF' (10uL 带过滤芯)，并相应修改代码。")

  finally:
    # 5. 断开连接
    print("正在关闭与 Vantage 的连接...")
    if hasattr(lh, '_setup_finished') and lh._setup_finished:
      await lh.stop()
    print("连接已关闭。")

if __name__ == "__main__":
  asyncio.run(main())
