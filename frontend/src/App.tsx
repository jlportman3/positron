import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import DeviceDetail from './pages/DeviceDetail'
import Endpoints from './pages/Endpoints'
import EndpointDetail from './pages/EndpointDetail'
import Subscribers from './pages/Subscribers'
import SubscriberDetail from './pages/SubscriberDetail'
import Bandwidths from './pages/Bandwidths'
import Alarms from './pages/Alarms'
import Users from './pages/Users'
import Firmware from './pages/Firmware'
import Groups from './pages/Groups'
import Settings from './pages/Settings'
import AuditLogs from './pages/AuditLogs'
import Notifications from './pages/Notifications'
import Ports from './pages/Ports'
import Timezones from './pages/Timezones'
import Sessions from './pages/Sessions'
import SystemInfo from './pages/SystemInfo'
import Logs from './pages/Logs'
import MySettings from './pages/MySettings'
import AcceptInvite from './pages/AcceptInvite'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/accept-invite" element={<AcceptInvite />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/devices" element={<Devices />} />
                <Route path="/devices/:id" element={<DeviceDetail />} />
                <Route path="/endpoints" element={<Endpoints />} />
                <Route path="/endpoints/:id" element={<EndpointDetail />} />
                <Route path="/subscribers" element={<Subscribers />} />
                <Route path="/subscribers/:id" element={<SubscriberDetail />} />
                <Route path="/bandwidths" element={<Bandwidths />} />
                <Route path="/alarms" element={<Alarms />} />
                <Route path="/users" element={<Users />} />
                <Route path="/firmware" element={<Firmware />} />
                <Route path="/groups" element={<Groups />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/audit-logs" element={<AuditLogs />} />
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/ports" element={<Ports />} />
                <Route path="/timezones" element={<Timezones />} />
                <Route path="/sessions" element={<Sessions />} />
                <Route path="/system-info" element={<SystemInfo />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/my-settings" element={<MySettings />} />
                <Route path="/firmware/add" element={<Navigate to="/firmware?upload=true" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
