# Product Context: Positron GAM Management System

## Why This Project Exists

ISPs using Positron GAM equipment face high licensing costs for VIRTUOSO Domain Controller, which is required for centralized management of multiple GAM devices. This creates a barrier for medium-scale deployments (11-50 devices) where the licensing cost becomes significant relative to the infrastructure investment.

## Problems It Solves

### Primary Problems
1. **High Licensing Costs**: VIRTUOSO pricing makes centralized management expensive for medium deployments
2. **Vendor Lock-in**: Dependence on Positron's proprietary management platform
3. **Limited Integration**: Restricted integration options with existing ISP billing systems
4. **Manual Processes**: Without centralized management, subscriber provisioning becomes manual and error-prone

### Secondary Problems
1. **Scalability Barriers**: Cost increases linearly with device count
2. **Feature Limitations**: Cannot customize workflows to specific ISP needs
3. **Data Silos**: Subscriber data trapped in proprietary system
4. **Deployment Complexity**: VIRTUOSO requires specific infrastructure setup

## How It Should Work

### Core User Experience
1. **Single Dashboard**: Manage all GAM devices from one web interface
2. **Automated Sync**: Billing system changes automatically provision/deprovision services
3. **Zero-Touch Provisioning**: New subscribers get service without manual GAM configuration
4. **Real-Time Monitoring**: Immediate visibility into device health and subscriber status

### Key Workflows

#### Subscriber Onboarding
1. Customer added to Sonar/Splynx billing system
2. System automatically detects new customer via webhook/sync
3. Available GAM port identified and reserved
4. Service provisioned on GAM device via SNMP/SSH
5. Customer receives service without manual intervention

#### Service Changes
1. Billing system plan change triggers webhook
2. System updates bandwidth limits on GAM device
3. Changes take effect immediately
4. Audit trail maintained for all changes

#### Device Management
1. GAM devices discovered automatically via network scan
2. Device health monitored continuously via SNMP
3. Alerts generated for device issues
4. Firmware updates coordinated across fleet

## User Experience Goals

### For ISP Administrators
- **Simplicity**: Single interface for all GAM management tasks
- **Reliability**: System works consistently without manual intervention
- **Visibility**: Clear status of all devices and subscribers
- **Control**: Ability to override automated processes when needed

### For ISP Technicians
- **Efficiency**: Faster subscriber provisioning and troubleshooting
- **Clarity**: Clear diagnostic information for service issues
- **Automation**: Reduced manual configuration tasks
- **Integration**: Works seamlessly with existing tools and processes

### For ISP Management
- **Cost Savings**: Eliminate VIRTUOSO licensing costs
- **Scalability**: System grows with business without linear cost increase
- **Flexibility**: Customize workflows to business needs
- **Independence**: Reduce vendor dependency

## Success Metrics

### Technical Metrics
- **Provisioning Time**: < 5 minutes from billing system to active service
- **Uptime**: 99.9% system availability
- **Sync Accuracy**: 100% billing system synchronization
- **Device Coverage**: Support for all GAM models (12/24 port, copper/coax)

### Business Metrics
- **Cost Reduction**: Eliminate VIRTUOSO licensing fees
- **Operational Efficiency**: 80% reduction in manual provisioning tasks
- **Error Reduction**: 90% fewer provisioning errors
- **Time to Market**: Faster new subscriber activation

### User Experience Metrics
- **Interface Usability**: < 30 seconds to complete common tasks
- **Learning Curve**: New users productive within 1 hour
- **Error Recovery**: Clear guidance for resolving issues
- **Mobile Access**: Responsive design for mobile device management
