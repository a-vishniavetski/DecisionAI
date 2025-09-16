// frontend/src/App.jsx
import { useState, useEffect } from 'react'

function App() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    fetch('/api/hello')
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(err => setMessage('Error loading message'))
  }, [])

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>🚀 FastAPI + React</h1>
      <p>Frontend: Hello from React!</p>
      <p>Backend: {message}</p>
      <div style={{ marginTop: '2rem', color: '#666' }}>
        <p>✅ Single Docker container</p>
        <p>✅ FastAPI backend serving API</p>
        <p>✅ React frontend making API calls</p>
      </div>
    </div>
  )
}

export default App