import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { PageLoader } from '@/components/ui/Spinner'

// Lazy-load pages for code splitting
const LoginPage           = lazy(() => import('@/pages/LoginPage'))
const RegisterPage        = lazy(() => import('@/pages/RegisterPage'))
const DashboardPage       = lazy(() => import('@/pages/DashboardPage'))
const ProfilePage         = lazy(() => import('@/pages/ProfilePage'))
const ResumesPage         = lazy(() => import('@/pages/ResumesPage'))
const TargetRolePage      = lazy(() => import('@/pages/TargetRolePage'))
const PreparationPage     = lazy(() => import('@/pages/PreparationPage'))
const SessionsPage        = lazy(() => import('@/pages/SessionsPage'))
const InterviewPage       = lazy(() => import('@/pages/InterviewPage'))
const InterviewHistoryPage = lazy(() => import('@/pages/InterviewHistoryPage'))
const NotFoundPage        = lazy(() => import('@/pages/NotFoundPage'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes — wrapped in AppLayout */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard"        element={<DashboardPage />} />
            <Route path="/sessions"         element={<SessionsPage />} />
            <Route path="/interview/sessions" element={<SessionsPage />} />
            <Route path="/profile"          element={<ProfilePage />} />
            <Route path="/resumes"          element={<ResumesPage />} />
            <Route path="/target-roles"     element={<TargetRolePage />} />
            <Route path="/preparation"      element={<PreparationPage />} />
            <Route path="/interview/new"    element={<InterviewPage />} />
            <Route path="/interview/:id"    element={<InterviewPage />} />
            <Route path="/interview/history/:id" element={<InterviewHistoryPage />} />
          </Route>

          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
