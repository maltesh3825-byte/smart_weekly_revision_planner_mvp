import React from 'react'
import { useLocation } from 'react-router-dom'

export default function Questions() {
  const loc = useLocation()
  const { questions } = loc.state || {}

  if (!questions) return (
    <div className="container">
      <p>No questions available. Generate a plan first.</p>
    </div>
  )

  return (
    <div className="container">
      <h2>Generated Questions</h2>

      <h3>MCQs (6)</h3>
      {questions.mcqs && questions.mcqs.map((m, i) => (
        <div key={i} className="mcq">
          <strong>{i+1}. {m.question}</strong>
          <ul>
            {m.options && m.options.map((o, idx) => <li key={idx}>{String.fromCharCode(65+idx)}. {o}</li>)}
          </ul>
        </div>
      ))}

      <h3>Short Answer Questions (2)</h3>
      {questions.short_questions && questions.short_questions.map((s, i) => (
        <div key={i} className="card">
          <strong>{i+1}. {s.question}</strong>
          <div>Answer: {s.answer}</div>
        </div>
      ))}

      <h3>Long Answer Questions (2)</h3>
      {questions.long_questions && questions.long_questions.map((l, i) => (
        <div key={i} className="card">
          <strong>{i+1}. {l.question}</strong>
          <div>Answer: {l.answer}</div>
        </div>
      ))}
    </div>
  )
}
