import { getPrismaClient } from "../../../src/lib/db";

export default async function AdminDashboard() {
  const prisma = getPrismaClient();
  const questionCount = await prisma.question.count();
  const subjectCount = await prisma.subject.count();

  return (
    <main>
      <div className="card">
        <h1 className="section-title">Admin Dashboard</h1>
        <p>Welcome! Use the API endpoints to manage questions.</p>
        <div className="flex">
          <span className="status">Subjects: {subjectCount}</span>
          <span className="status">Questions: {questionCount}</span>
        </div>
        <h2>Available endpoints</h2>
        <ul>
          <li>POST /api/admin/import-json</li>
          <li>GET /api/admin/questions</li>
          <li>POST /api/admin/questions</li>
        </ul>
      </div>
    </main>
  );
}
