import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import GAMDeviceList from './components/GAM/GAMDeviceList'
import GAMDeviceDetail from './components/GAM/GAMDeviceDetail'
import SubscriberList from './components/Subscribers/SubscriberList'
import ProvisioningPage from './components/Provisioning/ProvisioningPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/devices" element={<GAMDeviceList />} />
        <Route path="/devices/:deviceId" element={<GAMDeviceDetail />} />
        <Route path="/subscribers" element={<SubscriberList />} />
        <Route path="/provisioning" element={<ProvisioningPage />} />
      </Routes>
    </Layout>
  )
}

export default App
