export type UiLang = "en" | "zh";

export const LANG_KEY = "labscriptai.lang";

const ZH: Record<string, string> = {
  "Couldn't reach the server. Check your connection and try again.": "无法连接服务，请检查网络后重试。",
  "This session has expired. Start a new protocol.": "这段会话已过期，请点击“更换仪器”开始新的实验协议。",
  "Too many requests. Please wait a moment and try again.": "请求较多，请稍等片刻后重试。",
  "Please check the experiment description or instrument and try again.": "请检查实验描述或仪器选择后重试。",
  "The service is temporarily unavailable. Please try again later.": "服务暂时不可用，请稍后重试。",
  "Something went wrong. Please try again.": "遇到问题，请重试。",
  "From experiment to robot protocol": "从实验想法到机器人协议",
  "Create a robot protocol": "创建机器人实验协议",
  "Describe your experiment. Review the plan in chat, then generate and check your script.": "描述实验，在聊天中核对方案，再生成并检查代码。",
  "Try an example": "先试一个示例",
  "Examples use Flex unless you choose another instrument.": "示例默认使用 Flex；也可先选择其他仪器。",
  "1. Choose your instrument": "1. 选择仪器",
  "2. Describe the experiment": "2. 描述实验",
  "Include volumes, reagents, and source and destination wells.": "请说明体积、试剂，以及来源孔和目标孔。",
  "SOP or existing code (optional)": "已有 SOP 或代码（可选）",
  "Paste your SOP, experimental steps, or robot code here.": "在这里粘贴 SOP、实验步骤或机器人代码。",
  "Attach a file": "上传文件",
  "Reading file…": "正在读取文件…",
  "Text files: .txt, .md, .py, .json": "支持文本文件：.txt、.md、.py、.json",
  "Could not read that file. Paste its contents below or try another file.": "文件读取失败。请直接粘贴内容，或换一个文件。",
  "Choose an instrument or try an example to begin.": "先选择仪器，或点击示例开始。",
  "Add an experiment description to continue.": "请填写实验描述后继续。",
  "You can review and change the plan before code is generated.": "生成代码前，可以先核对和修改实验方案。",
  "Create protocol": "创建实验协议",
  "Transfer 50 µL A1→B1": "转移 50 µL：A1 → B1",
  "Prepare a PCR mix": "配制 PCR 体系",
  "Serial dilution": "梯度稀释",
  "Transfer 50 µL from well A1 to B1 on a 96-well plate.": "在 96 孔板上，从 A1 孔转移 50 µL 到 B1 孔。",
  "Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.": "配制 PCR 体系：向 8 个样品孔各分配 20 µL 预混液。",
  "Dispense 20 µL of master mix into 8 sample wells.": "向 8 个样品孔各分配 20 µL 预混液。",
  "Prepare a 1:2 serial dilution across wells A1 to A8, with 100 µL in each well after mixing.": "在 A1 至 A8 孔进行 1:2 梯度稀释，混匀后每孔保留 100 µL。",
  "Use a 96-well plate. Ask me to confirm the stock, diluent and starting volume before generating code.": "使用 96 孔板。生成代码前，请先让我确认原液、稀释液和初始体积。",
  "Ready to create": "可以开始",
  "Preview temporarily unavailable": "预览服务暂不可用",
  "Service temporarily unavailable": "服务暂不可用，请稍后重试",
  "Your experiment, step by step": "看清实验的每一步",
  "Start with an experiment description or an SOP. Your plan, checks, and supported previews will appear here.": "输入实验描述或已有 SOP，这里会显示方案、检查结果和支持的预演。",
  "Review the plan": "核对实验方案",
  "Confirm volumes, wells, and equipment in chat.": "在聊天中确认体积、孔位和设备。",
  "Generate and check": "生成并检查代码",
  "Inspect the script and resolve reported issues.": "查看生成的代码，处理检查发现的问题。",
  "Preview and download": "预演并下载",
  "Explore supported steps and save your protocol.": "查看支持的操作预演，保存实验协议。",
  "No installation or robot connection needed to try the web demo.": "直接在网页中试用，无需安装或连接机器人。",
  "On-screen preview only": "仅屏幕预览",
  "On-screen deck": "屏幕台面",
  "Ready to watch": "可以观看",
  "In progress": "进行中",
  "Checks passed": "校验通过",
  "Checks failed": "校验未通过",
  "Cannot verify": "无法校验",
  "Missing deck details": "缺少台面信息",
  "Quick check": "快速确认",
  "Which robot — OT-2, Flex, Hamilton STAR, Hamilton Vantage, or Tecan Fluent?":
    "选择仪器 — OT-2、Flex、Hamilton STAR、Hamilton Vantage 或 Tecan Fluent？",
  "Downloadable script": "可下载脚本",
  "Downloadable worklist": "可下载工作表",
  "e.g. Transfer 50 µL from well A1 to B1": "例如：从 A1 孔转移 50 µL 到 B1",
  "Change robot": "更换仪器",
  "3D": "三维",
  "Notes attached": "已附备注",
  "Preview service down — OT-2 and Flex scripts stay off": "预览服务未启动 — OT-2 与 Flex 脚本暂不可用",
  "preview down": "预览不可用",
  "No DeepSeek key": "未配置 DeepSeek 密钥",
  "preview ready": "预览就绪",
  "Which robot?": "选择哪台仪器？",
  "Pick a robot.": "请先选择仪器。",
  "What should we run?": "要做什么实验？",
  "Notes (optional)": "备注（可选）",
  "or attach a file": "或上传文件",
  "Paste a draft, or leave blank": "可粘贴草稿，也可留空",
  "Let’s go": "开始",
  "Starting…": "正在开始…",
  "Volume, wells, or a confirm…": "体积、孔位，或确认…",
  Send: "发送",
  Thinking: "思考中",
  Writing: "正在写",
  Stage: "台面",
  Activity: "过程",
  Files: "文件",
  Deck: "台面",
  "The bench shows here.": "实验台预览会出现在这里。",
  "Watch the protocol": "观看实验流程",
  Close: "关闭",
  "Opening…": "正在打开…",
  "Transfer steps": "移液步骤",
  "Protocol summary": "方案摘要",
  Consumables: "耗材",
  Steps: "步骤",
  "Demo steps": "演示步骤",
  Download: "下载",
  History: "记录",
  "Hide runs": "收起记录",
  "Show runs": "展开记录",
  "Downloads land here.": "下载会出现在这里。",
  "Downloads after checks.": "校验通过后可下载。",
  "Executable downloads are available after checks pass.": "可执行文件需校验通过后才能下载。",
  "Nothing to download yet.": "还没有可下载的文件。",
  "Lab-check details": "校验细节",
  "Resize chat": "调整对话宽度",
  "Right stage": "右侧台面",
  Language: "语言",
  English: "English",
  中文: "中文",
  "Current step": "当前步骤",
  "Previous steps stay listed": "已完成步骤仍保留",
  "Demo progress": "演示进度",
  "Approximate steps": "约计步骤",
  Pipettes: "移液器",
  "No consumables listed yet.": "还没有耗材清单。",
  "Steps not listed yet": "步骤尚未列出",
  "liquid-handling step": "个移液步骤",
  "liquid-handling steps": "个移液步骤",
  step: "步",
  steps: "步骤",
  tips: "枪头",
  "PCR plate": "PCR 板",
  reservoir: "储液槽",
  trash: "废液槽",
  Trash: "废液槽",
  plate: "孔板",
  thermocycler: "热循环仪",
  labware: "耗材",
  "300 µL tips": "300 µL 枪头",
  "1000 µL tips": "1000 µL 枪头",
  "96-well plate": "96 孔板",
  "12-well reservoir": "12 孔储液槽",
  "200 µL DiTi tips": "200 µL DiTi 枪头",
  "Standard deck": "标准台面",
  "96-well PCR plate": "96 孔 PCR 板",
  "The deck preview fills this pane after checks pass.": "校验通过后，台面预览会填满此栏。",
  "The bench preview fills this pane after checks pass.": "校验通过后，实验台预览会填满此栏。",
  "The bench preview stays off while the preview service is down.": "预览服务未启动时，实验台预览保持关闭。",
  "Opening the bench preview…": "正在打开实验台预览…",
  Done: "完成",
};

export function parseUiLang(value: unknown): UiLang {
  const raw = String(value ?? "").trim().toLowerCase();
  if (raw === "zh" || raw === "zh-cn" || raw === "zh-hans" || raw === "chinese" || raw === "中文") {
    return "zh";
  }
  return "en";
}

export function loadUiLang(): UiLang {
  try {
    return parseUiLang(localStorage.getItem(LANG_KEY));
  } catch {
    return "en";
  }
}

export function saveUiLang(lang: UiLang): void {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch {
    /* ignore */
  }
}

export function t(en: string, lang: UiLang): string {
  if (lang === "zh") return ZH[en] ?? en;
  return en;
}
