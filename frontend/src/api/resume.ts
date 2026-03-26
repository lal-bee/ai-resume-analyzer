import { http } from "./client";

export async function parseResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await http.post("/api/resumes/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function matchResume(resumeId: string, jobDescription: string) {
  const { data } = await http.post("/api/resumes/match", {
    resume_id: resumeId,
    job_description: jobDescription,
  });
  return data;
}

