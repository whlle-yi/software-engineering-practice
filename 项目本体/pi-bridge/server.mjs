// pi-bridge：把开源 pi agent harness（earendil-works/pi）内置为排课系统的智能体引擎。
// 职责：接收 Flask /api/agent/chat 的委托 → 用 pi 的 Agent 循环驱动排课白名单工具 → 返回最终回答。
// 安全边界：工具一律回调 Flask /api/agent/bridge-tool（服务令牌校验），白名单/待确认项/审计仍在 Flask 侧。
// 配置（环境变量）：
//   PI_BRIDGE_PORT   桥监听端口（默认 8710）
//   FLASK_URL        Flask 后端地址（默认 http://127.0.0.1:5000）
//   PI_BRIDGE_TOKEN  桥↔Flask 服务令牌（两端须一致）
//   PI_PROVIDER      pi-ai provider id（默认 zai=智谱；亦支持 openai/deepseek/moonshot 等或任意 OpenAI 兼容端点）
//   PI_MODEL         模型 id（默认 glm-4-flash）
//   PI_BASE_URL      自定义 OpenAI 兼容端点（可选）
//   PI_API_KEY       LLM API key（缺省时 /chat 返回 503 提示，骨架其余功能正常）
import http from "node:http";
import { Agent } from "@earendil-works/pi-agent-core";
import { builtinModels } from "@earendil-works/pi-ai/providers/all";

const PORT = Number(process.env.PI_BRIDGE_PORT || 8710);
const FLASK = process.env.FLASK_URL || "http://127.0.0.1:5000";
const BRIDGE_TOKEN = process.env.PI_BRIDGE_TOKEN || "";
const PROVIDER = process.env.PI_PROVIDER || "zai";
const MODEL_ID = process.env.PI_MODEL || "glm-4-flash";
const API_KEY = process.env.PI_API_KEY || process.env.LLM_API_KEY || "";

const SYSTEM_PROMPT =
  "你是高校排课系统的内置智能体 PiAgent，只能通过提供的工具操作排课业务。" +
  "查询类工具直接调用并组织回答；涉及写操作（提交偏好/约束）时必须调用对应工具生成待确认项，" +
  "由管理员确认后生效。回答使用简体中文，简洁准确。";

// 排课白名单工具（与 Flask services/agent.py 的 WHITELIST 同名同参）：
// execute 统一回调 Flask bridge-tool 端点，复用其角色白名单/待确认项/审计安全壳。
function tool(name, description, parameters) {
  return {
    name,
    description,
    parameters,
    execute: async (_toolCallId, params) => {
      const res = await fetch(`${FLASK}/api/agent/bridge-tool`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Bridge-Token": BRIDGE_TOKEN },
        body: JSON.stringify({ name, args: params }),
      });
      const data = await res.json();
      if (data.code !== 0) throw new Error(data.message || "工具执行失败");
      return {
        content: [{ type: "text", text: JSON.stringify(data.data) }],
        details: data.data,
      };
    },
  };
}

const TOOLS = [
  tool("query_course_count", "统计课程数量", { type: "object", properties: {}, required: [] }),
  tool("query_teacher_count", "统计教师数量", { type: "object", properties: {}, required: [] }),
  tool("query_schedule_stats", "按视图统计课表记录数", {
    type: "object",
    properties: { view: { type: "string", description: "视图：class/teacher/room" }, ref: { type: "string" } },
    required: ["view"],
  }),
  tool("query_teacher_schedule", "查询教师课表（管理员可指定教师编号，教师角色默认本人）", {
    type: "object",
    properties: { teacher_no: { type: "string", description: "教师编号，如 T001" } },
    required: [],
  }),
  tool("query_class_schedule", "查询班级课表（学生角色专用）", { type: "object", properties: {}, required: [] }),
  tool("save_teacher_preference", "提交教师排课偏好待确认项（确认后生效）", {
    type: "object",
    properties: {
      teacher_no: { type: "string", description: "教师编号（管理员需指定）" },
      ptype: { type: "string", description: "prefer/avoid/consecutive" },
      content: { type: "string", description: "偏好内容，如 周二上午" },
      priority: { type: "string", description: "优先级 1-7，数字越小越高" },
    },
    required: ["ptype", "content"],
  }),
  tool("save_constraint", "保存排课软约束待确认项（确认后生效）", {
    type: "object",
    properties: {
      key: { type: "string", description: "prefer_day/avoid_day/max_daily" },
      params: { type: "string", description: "参数 JSON，如 {\"day\":\"周五\"}" },
      priority: { type: "string", description: "优先级 1-7" },
    },
    required: ["key", "params"],
  }),
];

function hasKey() {
  return Boolean(API_KEY);
}

function buildAgent() {
  const models = builtinModels();
  const model = models.getModel(PROVIDER, MODEL_ID);
  if (!model) throw new Error(`模型不存在：${PROVIDER}/${MODEL_ID}（检查 PI_PROVIDER/PI_MODEL）`);
  const agent = new Agent({
    initialState: { systemPrompt: SYSTEM_PROMPT, model },
    streamFn: models.streamSimple.bind(models),
  });
  agent.state.tools = TOOLS;
  return agent;
}

async function runChat(instruction, role) {
  if (!hasKey()) {
    return { answer: "（未配置 PI_API_KEY）pi 桥已就绪，但需要 LLM API key 才能运行真实对话。", pendings: [] };
  }
  const agent = buildAgent();
  let finalText = "";
  const pendings = [];
  agent.subscribe(event => {
    if (event.type === "message_end" && event.message?.role === "assistant") {
      for (const part of event.message.content || []) {
        if (part.type === "text") finalText += part.text;
      }
    }
    if (event.type === "tool_execution_end" && event.result?.details?.pending) {
      pendings.push(event.result.details);
    }
  });
  await agent.prompt(
    `${instruction}\n（当前用户角色：${role}。请据此选择合适的工具或直接回答。）`,
  );
  return { answer: finalText.trim() || "（无回答）", pendings };
}

const server = http.createServer(async (req, res) => {
  const json = (code, payload) => {
    res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(payload));
  };
  if (req.url === "/health") {
    return json(200, { ok: true, engine: "pi", provider: PROVIDER, model: MODEL_ID, keyConfigured: hasKey() });
  }
  if (req.method === "POST" && req.url === "/chat") {
    if (BRIDGE_TOKEN) {
      const token = req.headers["x-bridge-token"];
      if (token !== BRIDGE_TOKEN) return json(403, { code: "DENIED", message: "桥令牌无效" });
    }
    let body = "";
    for await (const chunk of req) body += chunk;
    let parsed;
    try {
      parsed = JSON.parse(body || "{}");
    } catch {
      return json(400, { code: "BAD_JSON", message: "请求体不是合法 JSON" });
    }
    try {
      const result = await runChat(parsed.instruction || "", parsed.role || "admin");
      return json(200, { code: 0, data: result });
    } catch (e) {
      return json(200, { code: "BRIDGE_ERROR", message: String(e.message || e) });
    }
  }
  json(404, { code: "NOT_FOUND", message: "未知端点" });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`pi-bridge 就绪：http://127.0.0.1:${PORT}（provider=${PROVIDER} model=${MODEL_ID} key=${hasKey() ? "已配置" : "未配置"}）`);
});
