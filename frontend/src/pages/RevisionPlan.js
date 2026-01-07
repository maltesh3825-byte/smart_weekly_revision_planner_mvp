import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function RevisionPlan() {
  const loc = useLocation()
  const nav = useNavigate()
  const { payload, result } = loc.state || {}

  const planDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  const weekend = ["Saturday", "Sunday"]

  if (!result) return (
    <div className="container">
      <p>No revision data. Please start from the home page.</p>
    </div>
  )

  const [loadingQ, setLoadingQ] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerateQuestions = async () => {
    setLoadingQ(true)
    setError(null)
    try {
      const body = { subject: payload?.subject, chapter: payload?.chapter, pages: payload?.pages, examType: payload?.examType, text: payload?.text, mode: 'questions' }
      const apiBase = process.env.REACT_APP_API_URL || 'http://localhost:5000'
      const res = await axios.post(`${apiBase}/generate-revision`, body)
      const data = res.data
      // navigate to Questions page with the returned questions
      nav('/questions', { state: { questions: data } })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingQ(false)
    }
  }

  return (
    <div className="container">
      <h2>Weekly Plan: {payload?.subject} — {payload?.chapter}</h2>
      <p>Time allocation: 30 minutes per subject per day.</p>

      <h3>Monday - Friday (Learning)</h3>
      <div className="plan-grid">
        {planDays.map(d => <div key={d} className="card">{d}: Learn new topics / examples</div>)}
      </div>

      <h3>Saturday - Sunday (Revision)</h3>
      <div className="plan-grid" style={{gridTemplateColumns: 'repeat(2,1fr)'}}>
        {weekend.map(d => <div key={d} className="card">{d}: Revise and practice problems</div>)}
      </div>

      <h3>30-minute Revision Summary</h3>
      <pre style={{whiteSpace:'pre-wrap'}}>{result.summary}</pre>

      <button onClick={handleGenerateQuestions} disabled={loadingQ}>{loadingQ ? 'Generating Questions...' : 'Generate Questions'}</button>
      {error && <p style={{color:'red'}}>{error}</p>}
    </div>
  )
}
