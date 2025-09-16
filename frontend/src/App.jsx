// frontend/src/App.jsx
import { useState, useEffect } from 'react'

function App() {
  const [message, setMessage] = useState('')
  const [responses, setResponses] = useState('')
  const [loading, setLoading] = useState(false)

  const  handleSubmit = async (e) => {
    e.preventDefault()

    console.log("unga bunga")

    if (!message.trim()) return

    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ user_question: message })
      })
      
      if (!response.ok) {
          throw new Error('API request failed')
      }
      
      const data = await response.json()
      setResponses(data.response)  
      setMessage('')  
        
    } catch (error) {
        console.error('Error:', error)
        alert('Something went wrong!')
        
    } finally {
        console.log(message)
        setLoading(false)  // Hide loading state
    }
  }

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
      <p>Backend: {responses}</p>
      <div style={{ marginTop: '2rem', color: '#666' }}>

      <form onSubmit={handleSubmit}>
        <input type="text" value={message} />
        <button type="submit">Send decision request</button>
      </form>

      </div>
    </div>
  )
}

export default App