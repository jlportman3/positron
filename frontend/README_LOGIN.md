# SmartGAM Login Feature

## Overview

The SmartGAM login system provides secure authentication with a modern, animated UI inspired by SmartOLT's design aesthetic. It features an animated network mesh background, Material-UI components, and JWT-based authentication.

## Features

### Visual Design
- **Animated Network Background**: Dynamic mesh network visualization with moving nodes and connections
- **Gradient Branding**: Blue gradient color scheme matching the SmartGAM brand
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Material-UI components with custom styling

### Authentication
- **JWT Token-Based Auth**: Uses OAuth2 password flow
- **Persistent Sessions**: Token stored in localStorage via Zustand persist middleware
- **Protected Routes**: Automatic redirect to login for unauthenticated users
- **Auto Token Validation**: Checks token validity on app load

### User Experience
- **Password Toggle**: Show/hide password visibility
- **Loading States**: Visual feedback during login process
- **Error Handling**: Clear error messages for login failures
- **Forgot Password Link**: Placeholder for password recovery (to be implemented)

## File Structure

```
frontend/src/
├── components/
│   ├── Login/
│   │   ├── Login.tsx                 # Main login page component
│   │   └── NetworkBackground.tsx     # Animated canvas background
│   └── Auth/
│       └── ProtectedRoute.tsx        # Route wrapper for authentication
├── store/
│   └── authStore.ts                  # Zustand authentication state
└── App.tsx                           # Updated with auth routes
```

## Components

### Login.tsx
Main login page with:
- Username/password form
- Submit handling with error display
- Responsive card layout
- SmartGAM branding

### NetworkBackground.tsx
Canvas-based animation featuring:
- 80 animated nodes
- Dynamic connections based on distance
- Smooth movement and edge bouncing
- Blue color scheme matching branding

### ProtectedRoute.tsx
Authentication wrapper that:
- Checks authentication state
- Redirects to `/login` if not authenticated
- Shows loading spinner during auth check

## State Management

### authStore.ts (Zustand)

**State:**
```typescript
{
  user: User | null           // Current user info
  token: string | null        // JWT access token
  isAuthenticated: boolean    // Auth status
  loading: boolean           // Loading state
}
```

**Actions:**
- `login(username, password)` - Authenticate user
- `logout()` - Clear auth state
- `checkAuth()` - Validate existing token
- `setToken(token)` - Update token

**Persistence:**
- Token and user stored in localStorage
- Auto-restored on page reload
- Token added to axios headers automatically

## API Integration

### Login Endpoint
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

Body:
  username=<username>
  password=<password>

Response:
  {
    "access_token": "jwt_token_here",
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "is_active": boolean,
      "is_superuser": boolean
    }
  }
```

### Authentication Header
All subsequent API requests include:
```
Authorization: Bearer <access_token>
```

## Usage

### Basic Setup

1. **Configure API URL** in `.env`:
```bash
VITE_API_URL=http://localhost:8001
```

2. **Start Development Server**:
```bash
npm run dev
```

3. **Access Login Page**:
Navigate to `http://localhost:3001/login`

### Protected Routes

Wrap routes that require authentication:

```typescript
<Route
  path="/protected"
  element={
    <ProtectedRoute>
      <Layout>
        <YourComponent />
      </Layout>
    </ProtectedRoute>
  }
/>
```

### Access User Info in Components

```typescript
import { useAuthStore } from '../store/authStore'

function MyComponent() {
  const { user, logout } = useAuthStore()

  return (
    <div>
      <p>Welcome, {user?.username}</p>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

## Layout Integration

The Layout component includes:
- **SmartGAM Branding**: Logo and name in app bar
- **User Menu**: Avatar with dropdown showing username/email
- **Logout**: Menu item to sign out
- **Gradient App Bar**: Matches login page aesthetic

## Styling

### Color Scheme
- **Primary Blue**: `#1976d2`
- **Secondary Blue**: `#42a5f5`
- **Dark Blue**: `#1565c0`
- **Background Gradient**: `135deg, #1a237e → #0d47a1 → #01579b`

### Animations
- **Network Nodes**: Smooth movement at 0.5px/frame
- **Connections**: Opacity based on distance (fade at 150px)
- **Login Card**: Blur backdrop with semi-transparent background
- **Buttons**: Hover effects with shadow elevation

## Backend Requirements

The frontend expects the backend to provide:

1. **Login Endpoint**: `/api/v1/auth/login`
   - OAuth2 password flow
   - Returns access token and user object

2. **User Info Endpoint**: `/api/v1/auth/me`
   - Validates token
   - Returns current user info

3. **CORS Configuration**:
   - Allow origin: `http://localhost:3001` (dev)
   - Allow credentials: `true`

## Security Considerations

### Implemented
- ✅ JWT token stored in localStorage (client-side)
- ✅ Token sent in Authorization header
- ✅ Protected routes check authentication
- ✅ Automatic logout on invalid token
- ✅ Password field with toggle visibility

### To Implement
- ⏳ Token refresh mechanism
- ⏳ Password reset functionality
- ⏳ Rate limiting on login attempts
- ⏳ Session timeout warnings
- ⏳ Two-factor authentication (optional)

## Development Notes

### Testing Login Flow

1. **Without Backend**:
   - Mock the auth API in `authStore.ts`
   - Use hardcoded test credentials

2. **With Backend**:
   - Ensure backend is running on port 8001
   - Create test user via backend seed/migration
   - Test login with real credentials

### Troubleshooting

**Login fails with network error**:
- Check `VITE_API_URL` in `.env`
- Verify backend is running
- Check CORS configuration

**Token not persisting**:
- Check browser localStorage
- Verify Zustand persist middleware config
- Clear browser cache/storage

**Protected routes not working**:
- Check `isAuthenticated` state in Redux DevTools
- Verify token is in axios headers
- Check `checkAuth()` is called on app load

## Future Enhancements

### Planned Features
- [ ] "Remember Me" checkbox
- [ ] Password strength indicator for registration
- [ ] Social login (Google, GitHub, etc.)
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Accessibility improvements (ARIA labels)

### Backend Integration
- [ ] User registration page
- [ ] Password reset flow
- [ ] Email verification
- [ ] Role-based access control (RBAC)
- [ ] Audit logging for login attempts

## Screenshots

### Login Page Features
- Animated mesh network background
- SmartGAM branded logo (SG in circle)
- Username and password fields
- Password visibility toggle
- "Forgot your password?" link
- Gradient login button
- Loading spinner during authentication
- Error alerts for failed login
- Version footer

### Post-Login
- SmartGAM branding in app bar
- User avatar with dropdown menu
- Logout option in menu
- Consistent gradient theme throughout app

## Dependencies

```json
{
  "zustand": "^4.4.7",           // State management with persistence
  "@mui/material": "^5.14.20",   // UI components
  "@mui/icons-material": "^5.14.19", // Icons
  "react-router-dom": "^6.20.0", // Routing with protected routes
  "axios": "^1.6.2"              // HTTP client with auth headers
}
```

## License

Part of the Positron GAM Management System - see main project LICENSE.
