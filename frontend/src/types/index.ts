export interface GAMDevice {
  id: string
  name: string
  ip_address: string
  model: string
  status: 'online' | 'offline' | 'error' | 'maintenance'
  location?: string
  firmware_version?: string
  uptime?: number
  cpu_usage?: number
  memory_usage?: number
}

export interface GAMPort {
  id: string
  port_number: number
  port_type: 'mimo' | 'siso' | 'coax'
  status: 'up' | 'down' | 'disabled' | 'error'
  enabled: boolean
  name?: string
}

export interface Subscriber {
  id: string
  name: string
  email: string
  phone?: string
  service_address: string
  status: 'pending' | 'active' | 'suspended' | 'cancelled'
  endpoint_mac?: string
  vlan_id?: number
  external_id?: string
}

export interface BandwidthPlan {
  id: string
  name: string
  description: string
  downstream_mbps: number
  upstream_mbps: number
}

export interface ProvisioningRequest {
  subscriber_id: string
  gam_port_id: string
  bandwidth_plan_id: string
  vlan_id?: number
}
