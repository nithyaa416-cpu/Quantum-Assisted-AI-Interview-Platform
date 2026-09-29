import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { queryClient } from './queryClient'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            borderRadius: '10px',
          },
          success: { iconTheme: { primary: '#6366f1', secondary: '#f1f5f9' } },
          error:   { iconTheme: { primary: '#ef4444', secondary: '#f1f5f9' } },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>,
)
