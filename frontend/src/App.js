import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import RevisionInput from './pages/RevisionInput'
import RevisionPlan from './pages/RevisionPlan'
import Questions from './pages/Questions'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/input" element={<RevisionInput />} />
        <Route path="/plan" element={<RevisionPlan />} />
        <Route path="/questions" element={<Questions />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
