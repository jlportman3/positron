import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import GAMDeviceList from './components/GAM/GAMDeviceList'
import GAMDeviceDetail from './components/GAM/GAMDeviceDetail'
import AddGAMDevice from './components/GAM/AddGAMDevice'
import SubscriberList from './components/Subscribers/SubscriberList'
import ProvisioningPage from './components/Provisioning/ProvisioningPage'
import SettingsPage from './components/Settings/SettingsPage'
import UnconfiguredCPEList from './components/CPE/UnconfiguredCPEList'
import ConfiguredCPEList from './components/CPE/ConfiguredCPEList'
import Login from './components/Login/Login'
import ProtectedRoute from './components/Auth/ProtectedRoute'
import { useAuthStore } from './store/authStore'

function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login />
        }
      />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/devices"
        element={
          <ProtectedRoute>
            <Layout>
              <GAMDeviceList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/devices/new"
        element={
          <ProtectedRoute>
            <Layout>
              <AddGAMDevice />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/devices/:deviceId"
        element={
          <ProtectedRoute>
            <Layout>
              <GAMDeviceDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/unconfigured"
        element={
          <ProtectedRoute>
            <Layout>
              <UnconfiguredCPEList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/configured"
        element={
          <ProtectedRoute>
            <Layout>
              <ConfiguredCPEList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subscribers"
        element={
          <ProtectedRoute>
            <Layout>
              <SubscriberList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/provisioning"
        element={
          <ProtectedRoute>
            <Layout>
              <ProvisioningPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <SettingsPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
