<template>
  <main class="container">
    <h1>AI Resume Analyzer</h1>
    <p class="subtitle">上传 PDF 简历，结构化提取并评估岗位匹配度。</p>

    <ResultPanel title="1) 上传简历">
      <input type="file" accept=".pdf" @change="onFileChange" />
      <div class="actions">
        <button :disabled="!selectedFile || parsing" @click="handleParse">
          {{ parsing ? "解析中..." : "解析简历" }}
        </button>
      </div>
      <StatusAlert :message="parseMessage" :type="parseMessageType" />
    </ResultPanel>

    <ResultPanel title="2) 输入岗位描述">
      <textarea
        v-model="jobDescription"
        placeholder="请输入岗位职责、技术要求、年限和学历要求..."
      />
      <div class="actions">
        <button :disabled="!parseResult?.resume_id || !jobDescription.trim() || matching" @click="handleMatch">
          {{ matching ? "匹配中..." : "开始匹配" }}
        </button>
      </div>
      <StatusAlert :message="matchMessage" :type="matchMessageType" />
    </ResultPanel>

    <ResultPanel v-if="parseResult" title="3) 解析结果">
      <p><strong>resume_id:</strong> {{ parseResult.resume_id }}</p>
      <p><strong>提取模式:</strong> {{ parseResult.parsed_info.extraction_mode }}</p>
      <p><strong>命中缓存:</strong> {{ parseResult.from_cache ? "是" : "否" }}</p>

      <h4>基础信息</h4>
      <ul>
        <li>姓名：{{ parseResult.parsed_info.name || "-" }}</li>
        <li>电话：{{ parseResult.parsed_info.phone || "-" }}</li>
        <li>邮箱：{{ parseResult.parsed_info.email || "-" }}</li>
        <li>地址：{{ parseResult.parsed_info.address || "-" }}</li>
        <li>求职意向：{{ parseResult.parsed_info.job_intention || "-" }}</li>
        <li>期望薪资：{{ parseResult.parsed_info.expected_salary || "-" }}</li>
        <li>工作年限：{{ parseResult.parsed_info.work_years || "-" }}</li>
        <li>学历：{{ parseResult.parsed_info.education || "-" }}</li>
      </ul>

      <h4>项目经历</h4>
      <div v-if="parseResult.parsed_info.projects.length === 0">暂无提取项目</div>
      <ul v-else>
        <li v-for="(project, idx) in parseResult.parsed_info.projects" :key="idx">
          {{ project.name || "未命名项目" }} {{ project.description ? ` - ${project.description}` : "" }}
        </li>
      </ul>

      <h4>清洗文本预览</h4>
      <pre>{{ parseResult.clean_text.slice(0, 1200) }}{{ parseResult.clean_text.length > 1200 ? "\n...(已截断)" : "" }}</pre>
    </ResultPanel>

    <ResultPanel v-if="matchResult" title="4) 匹配结果">
      <p><strong>匹配分数：</strong>{{ matchResult.match_score }}</p>
      <p><strong>命中缓存：</strong>{{ matchResult.from_cache ? "是" : "否" }}</p>
      <p><strong>评分维度：</strong>{{ matchResult.dimension_scores }}</p>
      <p><strong>岗位关键词：</strong>{{ matchResult.job_keywords.join("、") || "-" }}</p>
      <p><strong>命中关键词：</strong>{{ matchResult.matched_keywords.join("、") || "-" }}</p>
      <p><strong>缺失关键词：</strong>{{ matchResult.missing_keywords.join("、") || "-" }}</p>
      <p><strong>AI 总结：</strong>{{ matchResult.ai_summary }}</p>
    </ResultPanel>

    <div v-if="!parseResult && !parsing" class="empty">等待上传 PDF 并解析。</div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { parseResume, matchResume } from "./api/resume";
import ResultPanel from "./components/ResultPanel.vue";
import StatusAlert from "./components/StatusAlert.vue";

const selectedFile = ref<File | null>(null);
const jobDescription = ref("");
const parsing = ref(false);
const matching = ref(false);

const parseResult = ref<any>(null);
const matchResult = ref<any>(null);

const parseMessage = ref("");
const parseMessageType = ref<"error" | "info" | "success">("info");
const matchMessage = ref("");
const matchMessageType = ref<"error" | "info" | "success">("info");

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  parseMessage.value = "";
  matchMessage.value = "";
  matchResult.value = null;
  selectedFile.value = file || null;
}

async function handleParse() {
  if (!selectedFile.value) return;
  parseMessage.value = "";
  parsing.value = true;
  try {
    const data = await parseResume(selectedFile.value);
    parseResult.value = data;
    parseMessageType.value = "success";
    parseMessage.value = data.from_cache ? "解析完成（缓存命中）" : "解析完成";
  } catch (error: any) {
    parseMessageType.value = "error";
    parseMessage.value =
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      "解析失败，请检查后端日志";
  } finally {
    parsing.value = false;
  }
}

async function handleMatch() {
  if (!parseResult.value?.resume_id || !jobDescription.value.trim()) return;
  matchMessage.value = "";
  matching.value = true;
  try {
    const data = await matchResume(parseResult.value.resume_id, jobDescription.value.trim());
    matchResult.value = data;
    matchMessageType.value = "success";
    matchMessage.value = data.from_cache ? "匹配完成（缓存命中）" : "匹配完成";
  } catch (error: any) {
    matchMessageType.value = "error";
    matchMessage.value =
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      "匹配失败，请检查输入或后端日志";
  } finally {
    matching.value = false;
  }
}
</script>

<style scoped>
.container {
  max-width: 980px;
  margin: 24px auto;
  font-family: Arial, sans-serif;
  color: #0f172a;
}
h1 {
  margin-bottom: 6px;
}
.subtitle {
  margin-top: 0;
  color: #475569;
}
textarea {
  width: 100%;
  min-height: 120px;
  resize: vertical;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 10px;
  box-sizing: border-box;
}
.actions {
  margin-top: 10px;
}
button {
  border: 0;
  border-radius: 8px;
  padding: 10px 16px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
pre {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 280px;
  overflow: auto;
}
.empty {
  color: #64748b;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}
ul {
  margin: 6px 0 10px;
  padding-left: 20px;
}
</style>

