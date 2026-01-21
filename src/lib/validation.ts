export type ImportPayload = {
  subject?: string;
  category?: string | null;
  chapter?: string | null;
  questions: Array<{
    text: string;
    options: {
      A: string;
      B: string;
      C: string;
      D: string;
    };
    correct: "A" | "B" | "C" | "D";
  }>;
};

export function validateImportPayload(payload: unknown): payload is ImportPayload {
  if (!payload || typeof payload !== "object") {
    return false;
  }
  const record = payload as ImportPayload;
  if (!Array.isArray(record.questions) || record.questions.length === 0) {
    return false;
  }
  for (const question of record.questions) {
    if (!question || typeof question !== "object") {
      return false;
    }
    if (typeof question.text !== "string" || question.text.trim() === "") {
      return false;
    }
    if (!question.options) {
      return false;
    }
    const { A, B, C, D } = question.options;
    if (![A, B, C, D].every((option) => typeof option === "string" && option.trim() !== "")) {
      return false;
    }
    if (!["A", "B", "C", "D"].includes(question.correct)) {
      return false;
    }
  }
  return true;
}
