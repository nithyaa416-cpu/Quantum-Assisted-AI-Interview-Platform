import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { stopAllMediaStreams } from '@/utils/mediaStreamManager'
import { stopAllAudioAndSpeech } from '@/utils/audioSpeechManager'

const pageTitles: Record<string, string> = {
  '/dashboard':     'Dashboard',
  '/sessions':      'Interview Sessions',
  '/profile':       'My Profile',
  '/resumes':       'Resumes',
  '/target-roles':  'Target Roles',
  '/preparation':   'Preparation Plan',
  '/interview/new': 'Start Interview',
}

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const title = pageTitles[location.pathname] ?? 'QAIP'

  // Guarantee that camera, microphone hardware, and audio/speech are completely shut down on all main pages
  useEffect(() => {
    stopAllMediaStreams()
    stopAllAudioAndSpeech()
  }, [location.pathname])

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar collapsed={collapsed} />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar onToggleSidebar={() => setCollapsed((c) => !c)} title={title} />

        <main className="flex-1 overflow-y-auto p-6 animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
