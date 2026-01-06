import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function Home() {
  const nav = useNavigate()
  return (
    <div className="container center">
      <h1>Smart Weekly Revision Planner</h1>
      <p>Help Class 8 students plan weekly revision and prepare for FA/SA exams.</p>
      <button onClick={() => nav('/input')}>Start Revision</button>
    </div>
  )
}
