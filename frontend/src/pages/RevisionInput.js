import React, { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

export default function RevisionInput() {
  const [subject, setSubject] = useState('Maths')
  const [chapter, setChapter] = useState('')
  const [pages, setPages] = useState('')
  const [examType, setExamType] = useState('FA-1')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const nav = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const body = { subject, chapter, pages, examType, text, mode: 'summary' }
      const res = await axios.post('http://localhost:5000/generate-revision', body)
      const data = res.data
      nav('/plan', { state: { payload: { subject, chapter, pages, examType, text }, result: data } })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h2>Revision Input</h2>
      <form onSubmit={submit}>
        <div className="field">
          <label>Subject</label>
          <select value={subject} onChange={(e) => setSubject(e.target.value)}>
            <option>Maths</option>
            <option>Science</option>
            <option>English</option>
            <option>Social Studies</option>
          </select>
        </div>
        <div className="field">
          <label>Chapter Name</label>
          <input value={chapter} onChange={(e) => setChapter(e.target.value)} placeholder="e.g., Linear Equations" required />
        </div>
        <div className="field">
          <label>Pages Covered This Week</label>
          <input value={pages} onChange={(e) => setPages(e.target.value)} placeholder="e.g., pp. 10-24" />
        </div>

        <div className="field">
          <label>Paste Chapter Text Here (2-3 pages max)</label>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={10} placeholder="Paste textbook text here..." />
        </div>

        <div className="field">
          <label>Exam Type</label>
          <select value={examType} onChange={(e) => setExamType(e.target.value)}>
            <option>FA-1</option>
            <option>FA-2</option>
            <option>SA-1</option>
            <option>FA-3</option>
            <option>FA-4</option>
            <option>Final</option>
          </select>
        </div>
        <button type="submit" disabled={loading}>{loading ? 'Generating...' : 'Submit'}</button>
        {error && <p style={{color:'red'}}>{error}</p>}
      </form>
    </div>
  )
}
