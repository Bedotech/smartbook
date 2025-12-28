# Smartbook Frontend

Modern React frontend for the Smartbook group check-in and compliance management system.

## Architecture

This is a **monorepo** containing two applications and shared packages:

### Applications

- **Guest Portal** (`apps/guest`) - Mobile-first PWA for guests to complete check-in
- **Admin Dashboard** (`apps/admin`) - Desktop-first dashboard for hotel managers

### Shared Packages

- **@smartbook/ui** - Shared UI components (Button, Input, Card, etc.)
- **@smartbook/api** - API client for backend communication
- **@smartbook/utils** - Utility functions (date formatting, class names)
- **@smartbook/types** - TypeScript type definitions

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Routing**: React Router v6
- **State Management**: TanStack Query (server state) + Zustand (UI state)
- **Styling**: Tailwind CSS 3
- **Forms**: React Hook Form + Zod validation
- **PWA**: Vite PWA Plugin + Workbox
- **Package Manager**: pnpm 8 (workspaces)

## Prerequisites

- Node.js 20+
- pnpm 8+
- Docker & Docker Compose (for deployment)

## Getting Started

### Development

1. **Install dependencies**:
   ```bash
   cd frontend
   pnpm install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development servers**:

   Guest Portal (port 3000):
   ```bash
   pnpm dev:guest
   ```

   Admin Dashboard (port 3001):
   ```bash
   pnpm dev:admin
   ```

   Both apps simultaneously:
   ```bash
   pnpm dev
   ```

4. **Access the apps**:
   - Guest Portal: http://localhost:3000
   - Admin Dashboard: http://localhost:3001

### Production Build

Build both apps:
```bash
pnpm build
```

Build individual apps:
```bash
pnpm build:guest
pnpm build:admin
```

Preview production build:
```bash
cd apps/guest
pnpm preview
```

## Project Structure

```
frontend/
├── apps/
│   ├── guest/                 # Guest Portal PWA
│   │   ├── src/
│   │   │   ├── pages/        # Route pages
│   │   │   ├── components/   # Guest-specific components
│   │   │   ├── hooks/        # Custom hooks
│   │   │   ├── App.tsx       # Root component
│   │   │   └── main.tsx      # Entry point
│   │   ├── public/
│   │   │   └── manifest.json # PWA manifest
│   │   └── vite.config.ts
│   │
│   └── admin/                 # Admin Dashboard
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   ├── App.tsx
│       │   └── main.tsx
│       └── vite.config.ts
│
├── packages/
│   ├── ui/                    # Shared UI components
│   ├── api/                   # API client
│   ├── utils/                 # Utilities
│   └── types/                 # TypeScript types
│
├── docker/
│   ├── Dockerfile.guest       # Guest app Docker build
│   ├── Dockerfile.admin       # Admin app Docker build
│   └── nginx/                 # Nginx configs
│
├── package.json               # Root workspace config
├── pnpm-workspace.yaml        # pnpm workspaces
├── tsconfig.json              # Base TypeScript config
└── tailwind.config.js         # Tailwind config
```

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# App Configuration
VITE_APP_NAME=Smartbook
VITE_ENABLE_ANALYTICS=false

# Development
VITE_ENABLE_MOCK_API=false
```

## Available Scripts

From `frontend/` directory:

- `pnpm dev` - Start both apps in development mode
- `pnpm dev:guest` - Start Guest Portal only
- `pnpm dev:admin` - Start Admin Dashboard only
- `pnpm build` - Build both apps for production
- `pnpm build:guest` - Build Guest Portal only
- `pnpm build:admin` - Build Admin Dashboard only
- `pnpm lint` - Run ESLint
- `pnpm type-check` - Run TypeScript type checking

## Docker Deployment

From the **root** directory:

### Quick Start (Recommended)

```bash
./start.sh
```

This script will:
- Create `.env` files if they don't exist
- Build all Docker images
- Start all services (database, backend, guest app, admin app)
- Wait for services to be healthy
- Display access URLs

### Manual Docker Commands

Build images:
```bash
docker-compose build
```

Start services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

## Guest Portal (PWA)

### Features

- **Mobile-First Design**: Optimized for smartphones
- **Offline Support**: Service Worker caches pages and API responses
- **Magic Link Authentication**: No passwords required
- **Progressive Enhancement**: Works without JavaScript (basic functionality)
- **Touch-Friendly**: Minimum 48x48px touch targets
- **Autocomplete**: Italian municipalities and countries

### Routes

- `/s/:token` - Magic link entry (booking info + progress)
- `/s/:token/leader` - Group leader form (full document details)
- `/s/:token/members` - Member list + add member form
- `/s/:token/success` - Success page with QR code

### PWA Features

The Guest Portal is a fully installable Progressive Web App:

- **Offline-First**: Cached pages work without internet
- **Add to Home Screen**: Install like a native app
- **Push Notifications**: (Future) Check-in reminders
- **Background Sync**: (Future) Submit data when back online

### Testing PWA

1. Build the guest app: `pnpm build:guest`
2. Serve with HTTPS: `npx serve -s apps/guest/dist -l 3000`
3. Open in Chrome/Edge
4. Install via "Add to Home Screen"

## Admin Dashboard

### Features

- **Desktop-First Design**: Optimized for larger screens
- **Real-Time Updates**: TanStack Query with auto-refetch
- **Data Tables**: Sortable, filterable, paginated
- **Color-Coded Status**: Visual booking status indicators
- **One-Click Actions**: ROS1000 submit, tax calculation

### Routes

- `/` - Dashboard with statistics
- `/bookings` - Bookings list with filters
- `/bookings/:id` - Booking detail with guest management
- `/tax/reports` - Monthly/quarterly tax reports
- `/settings` - Tax rules and configuration

## API Integration

The `@smartbook/api` package provides typed API clients:

### Guest API

```typescript
import { guestApi } from '@smartbook/api'

// Get booking by magic link token
const booking = await guestApi.getBooking(token)

// Add group leader
const leader = await guestApi.addLeader(token, leaderData)

// Search municipalities
const municipalities = await guestApi.searchMunicipalities('Schil')
```

### Admin API

```typescript
import { adminApi } from '@smartbook/api'

// Get all bookings
const bookings = await adminApi.getBookings({ status: 'pending' })

// Submit to ROS1000
const result = await adminApi.submitROS1000(bookingId)

// Calculate tax
const tax = await adminApi.calculateTax(bookingId)
```

## State Management

### Server State (TanStack Query)

Used for all API data:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'

// Query
const { data, isLoading } = useQuery({
  queryKey: ['booking', token],
  queryFn: () => guestApi.getBooking(token)
})

// Mutation
const addLeader = useMutation({
  mutationFn: (data) => guestApi.addLeader(token, data),
  onSuccess: () => {
    queryClient.invalidateQueries(['booking', token])
  }
})
```

### UI State (Zustand)

Used for form drafts, preferences:

```typescript
import create from 'zustand'
import { persist } from 'zustand/middleware'

const useFormStore = create(
  persist(
    (set) => ({
      leaderData: {},
      setLeaderData: (data) => set({ leaderData: data })
    }),
    { name: 'form-storage' }
  )
)
```

## Styling with Tailwind CSS

### Utility Classes

```tsx
<button className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition">
  Click Me
</button>
```

### Custom Utilities

```tsx
// Mobile-friendly touch target
<button className="touch-target">Button</button>
// Renders: min-h-[48px] min-w-[48px]
```

### Using cn() Utility

```tsx
import { cn } from '@smartbook/utils'

<div className={cn(
  'base-class',
  isActive && 'active-class',
  error && 'error-class'
)} />
```

## Shared Components

### Button

```tsx
import { Button } from '@smartbook/ui'

<Button variant="primary" size="lg" isLoading={loading}>
  Submit
</Button>
```

### Input

```tsx
import { Input } from '@smartbook/ui'

<Input
  type="text"
  placeholder="Enter name"
  error={errors.name?.message}
/>
```

### Card

```tsx
import { Card } from '@smartbook/ui'

<Card>
  <h2>Title</h2>
  <p>Content</p>
</Card>
```

## Troubleshooting

### Port Already in Use

If port 3000 or 3001 is already in use:

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or change port in vite.config.ts
server: { port: 3002 }
```

### Module Not Found

If you get module resolution errors:

```bash
# Clean install
rm -rf node_modules
pnpm install
```

### Type Errors

Ensure TypeScript is using the workspace version:

```bash
# Check TypeScript version
pnpm tsc --version

# Restart TypeScript server in VSCode
Cmd+Shift+P > "TypeScript: Restart TS Server"
```

### PWA Not Updating

Clear service worker cache:

1. Open DevTools
2. Application tab > Service Workers
3. Click "Unregister"
4. Hard refresh (Cmd+Shift+R)

## Performance

### Lighthouse Scores (Target)

- Performance: 90+
- Accessibility: 100
- Best Practices: 95+
- SEO: 90+
- PWA: 100 (Guest Portal)

### Optimization Checklist

- [x] Code splitting (lazy loading routes)
- [x] Tree shaking (Vite automatic)
- [x] Image optimization
- [x] Gzip compression (Nginx)
- [x] Browser caching
- [x] Service Worker caching
- [ ] CDN for static assets (future)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile Safari 14+
- Chrome Android 90+

## Contributing

### Code Style

- Use TypeScript strict mode
- Follow ESLint rules
- Use Prettier for formatting
- Prefer functional components
- Use named exports

### Commit Messages

```
feat: Add tax calculation page
fix: Resolve municipality autocomplete bug
docs: Update API documentation
style: Format with Prettier
refactor: Extract Button component
test: Add booking form tests
```

## License

Proprietary - Bedotech Smartbook Project

## Support

For issues or questions, contact the development team or create an issue in the repository.
