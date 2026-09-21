export type UiLang = "en" | "zh";

export const LANG_KEY = "labscriptai.lang";

const ZH: Record<string, string> = {
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
  History: "记录",
  "Hide runs": "收起记录",
  "Show runs": "展开记录",
  "Downloads land here.": "下载会出现在这里。",
  "Downloads after checks.": "校验通过后可下载。",
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
