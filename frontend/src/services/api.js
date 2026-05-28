const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function analyzeCompany(name, about_text) {
  const res = await fetch(`${BASE}/companies/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_name: name, about_text }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateReport(company_id) {
  const res = await fetch(`${BASE}/reports/generate/${company_id}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitQuiz(report_id, answers) {
  const res = await fetch(`${BASE}/quiz/submit/${report_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
