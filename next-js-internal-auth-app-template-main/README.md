# Aspect Dashboard - Authentication Starter Template

A production-ready Next.js authentication starter template using Better Auth, featuring Microsoft and GitHub OAuth, PostgreSQL database via Neon, and custom Aspect brand colors.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Authentication System](#authentication-system)
- [Database Management](#database-management)
- [Custom Color System](#custom-color-system)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

This project started as a complex sales/marketing analytics dashboard but has been **simplified to a clean authentication starter template**. It provides a solid foundation for building authenticated web applications with:

- ✅ Production-ready OAuth authentication
- ✅ Secure session management
- ✅ PostgreSQL database integration
- ✅ Custom brand color system
- ✅ Clean, minimal UI
- ✅ Type-safe development with TypeScript

## Features

- 🔐 **Better Auth Integration** - Modern, secure authentication library
- 🌐 **Microsoft OAuth** - Enterprise SSO support
- 🐙 **GitHub OAuth** - Developer-friendly authentication
- 💾 **Neon PostgreSQL** - Serverless Postgres database
- 🎨 **Custom Color System** - Aspect brand colors configured in Tailwind
- ✨ **Protected Routes** - Server-side authentication checks
- 🚀 **Next.js 15** - Latest App Router features
- 📱 **Responsive Design** - Mobile-first approach

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Framework** | Next.js 15 with App Router & Turbopack |
| **Language** | TypeScript 5 |
| **Authentication** | Better Auth 1.3+ |
| **Database** | PostgreSQL via Neon |
| **ORM** | Prisma 6 |
| **Styling** | Tailwind CSS 4 |
| **Deployment** | Vercel (recommended) |

## Architecture Overview

### Authentication Flow

```
┌─────────┐      ┌──────────┐      ┌────────────┐      ┌──────────┐
│  User   │─────▶│  Login   │─────▶│   OAuth    │─────▶│ Provider │
│ Browser │      │   Page   │      │  Provider  │      │(MS/GitHub)│
└─────────┘      └──────────┘      └────────────┘      └──────────┘
     ▲                                    │                    │
     │                                    ▼                    │
     │              ┌────────────────────────────────────┐     │
     └──────────────│  Better Auth Callback Handler      │◀────┘
                    │  /api/auth/callback/{provider}     │
                    └────────────────────────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────────┐
                    │  Create Session & Store in DB      │
                    │  (Neon PostgreSQL)                 │
                    └────────────────────────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────────┐
                    │  Redirect to /dashboard            │
                    │  (Protected Route)                 │
                    └────────────────────────────────────┘
```

### Database Schema

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│    User     │       │   Session    │       │   Account   │
├─────────────┤       ├──────────────┤       ├─────────────┤
│ id          │◀──────│ userId       │       │ userId      │────┐
│ email       │       │ token        │       │ providerId  │    │
│ name        │       │ expiresAt    │       │ accessToken │    │
│ image       │       │ ipAddress    │       │ refreshToken│    │
│ createdAt   │       │ userAgent    │       │ createdAt   │    │
└─────────────┘       └──────────────┘       └─────────────┘    │
       ▲                                              │          │
       └──────────────────────────────────────────────┘          │
                                                                 │
                    ┌──────────────┐                            │
                    │ Verification │                            │
                    ├──────────────┤                            │
                    │ identifier   │                            │
                    │ value        │                            │
                    │ expiresAt    │                            │
                    └──────────────┘                            │
```

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Node.js 18+** installed ([Download](https://nodejs.org/))
- **Git** installed
- A **Neon** account ([Sign up](https://neon.tech))
- **Microsoft Azure AD** or **GitHub** OAuth app (optional, but recommended)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd aspect-sales-marketing-forecast-clone
```

#### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including Next.js, Prisma, Better Auth, and Tailwind CSS.

#### 3. Set Up Neon Database

1. Go to [Neon Console](https://console.neon.tech)
2. Click **"New Project"**
3. Choose a name (e.g., "aspect-auth")
4. Select a region close to your users
5. Click **"Create Project"**
6. In the Connection Details section:
   - Select **"Pooled connection"** (recommended for serverless)
   - Copy the connection string

#### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database Connection (Required)
# Get this from Neon Console -> Connection Details
DATABASE_URL="postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require"

# Microsoft OAuth (Optional - for enterprise SSO)
MICROSOFT_CLIENT_ID="your_application_client_id"
MICROSOFT_CLIENT_SECRET="your_client_secret_value"
MICROSOFT_TENANT_ID="your_tenant_id"

# GitHub OAuth (Optional - for developer authentication)
GITHUB_CLIENT_ID="your_github_oauth_client_id"
GITHUB_CLIENT_SECRET="your_github_oauth_client_secret"

# Application Base URL
NEXT_PUBLIC_BASE_URL="http://localhost:3000"
```

**Important Notes:**
- Never commit `.env` to version control (already in `.gitignore`)
- Use strong, unique secrets in production
- The pooled connection from Neon is optimized for serverless environments

#### 5. Set Up OAuth Providers

<details>
<summary><strong>Microsoft OAuth Setup</strong> (Click to expand)</summary>

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **"New registration"**
4. Fill in the details:
   - **Name**: "Aspect Dashboard" (or your app name)
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `http://localhost:3000/api/auth/callback/microsoft`
5. Click **"Register"**
6. Copy the **Application (client) ID** → Add to `.env` as `MICROSOFT_CLIENT_ID`
7. Copy the **Directory (tenant) ID** → Add to `.env` as `MICROSOFT_TENANT_ID`
8. Go to **Certificates & secrets** → **New client secret**
9. Add a description and choose expiry
10. Copy the **Value** (not ID) → Add to `.env` as `MICROSOFT_CLIENT_SECRET`

**For Production:**
Add the production callback URL: `https://yourdomain.com/api/auth/callback/microsoft`

</details>

<details>
<summary><strong>GitHub OAuth Setup</strong> (Click to expand)</summary>

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click **"OAuth Apps"** → **"New OAuth App"**
3. Fill in the details:
   - **Application name**: "Aspect Dashboard"
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`
4. Click **"Register application"**
5. Copy the **Client ID** → Add to `.env` as `GITHUB_CLIENT_ID`
6. Click **"Generate a new client secret"**
7. Copy the secret → Add to `.env` as `GITHUB_CLIENT_SECRET`

**For Production:**
Update the URLs to your production domain.

</details>

#### 6. Initialize the Database

```bash
# Generate Prisma Client
npx prisma generate

# Push schema to database (creates tables)
npx prisma db push

# Optional: Open Prisma Studio to view your database
npx prisma studio
```

#### 7. Start the Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

#### 8. Test the Application

1. Navigate to `http://localhost:3000`
2. You'll be redirected to `/login`
3. Click "Continue with Aspect account" (Microsoft) or GitHub
4. Complete OAuth authentication
5. You'll be redirected to `/dashboard` with your user info

## Authentication System

### How Better Auth Works

Better Auth is a modern authentication library that provides:

1. **Session Management**: Secure, HTTP-only cookie sessions
2. **OAuth Integration**: Built-in support for 50+ providers
3. **Database Adapters**: Direct integration with Prisma
4. **Type Safety**: Full TypeScript support

### Authentication Flow Explained

#### Server-Side Authentication (`lib/auth.ts`)

```typescript
export const auth = betterAuth({
  database: prismaAdapter(prisma, { provider: "postgresql" }),
  socialProviders: {
    microsoft: {
      clientId: process.env.MICROSOFT_CLIENT_ID,
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
      // ... additional config
    },
  },
  plugins: [nextCookies()], // Enables Next.js cookie handling
});
```

**Key Points:**
- Configured once on the server
- Connects directly to Neon PostgreSQL via Prisma
- Handles OAuth flow automatically
- Stores sessions securely in the database

#### Client-Side Authentication (`lib/auth-client.ts`)

```typescript
export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000",
});
```

**Usage in Components:**
```tsx
// In a client component
const handleLogout = async () => {
  await authClient.signOut({
    fetchOptions: {
      onSuccess: () => router.push("/login"),
    },
  });
};
```

#### Protected Routes

Every protected page follows this pattern:

```tsx
// app/dashboard/page.tsx
export default async function DashboardPage() {
  // 1. Get session from Better Auth
  const session = await auth.api.getSession({ headers: await headers() });

  // 2. Redirect if not authenticated
  if (!session) {
    redirect("/login");
  }

  // 3. Use session data
  return <div>Welcome, {session.user.name}!</div>;
}
```

**How It Works:**
1. **Server Component**: Runs on the server, not exposed to client
2. **Session Check**: Validates the session cookie against the database
3. **Redirect**: If no valid session, user goes to `/login`
4. **Secure**: User data never exposed until verified

### OAuth Callback Handling

The `/api/auth/[...all]/route.ts` handles all authentication routes:

```typescript
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

export const { GET, POST } = toNextJsHandler(auth);
```

**Handles:**
- `/api/auth/sign-in/social` - Initiates OAuth flow
- `/api/auth/callback/microsoft` - Microsoft callback
- `/api/auth/callback/github` - GitHub callback
- `/api/auth/sign-out` - Logout
- `/api/auth/session` - Get current session

## Database Management

### Why Neon?

Neon is a serverless PostgreSQL database that offers:

- ✅ **Instant setup** - No server management
- ✅ **Generous free tier** - Perfect for development
- ✅ **Branching** - Database branches like Git
- ✅ **Auto-scaling** - Scales to zero when idle
- ✅ **Connection pooling** - Built-in for serverless

### Prisma Schema Overview

```prisma
// User table - stores user profiles
model User {
  id            String    @id
  name          String
  email         String    @unique
  emailVerified Boolean   @default(false)
  image         String?
  sessions      Session[]  // One user, many sessions
  accounts      Account[]  // One user, many OAuth accounts
}

// Session table - manages active sessions
model Session {
  id        String   @id
  userId    String
  token     String   @unique  // Session token in cookie
  expiresAt DateTime
  ipAddress String?
  userAgent String?
  user      User     @relation(...)
}

// Account table - stores OAuth provider data
model Account {
  id                    String    @id
  userId                String
  providerId            String   // "microsoft" or "github"
  accessToken           String?  // For API calls to provider
  refreshToken          String?  // To refresh access token
  // ... other OAuth fields
}

// Verification table - email verification tokens
model Verification {
  id         String   @id
  identifier String   // Email address
  value      String   // Verification code
  expiresAt  DateTime
}
```

### Common Prisma Commands

```bash
# Generate TypeScript client from schema
npx prisma generate

# Push schema changes to database (dev)
npx prisma db push

# Create a migration (production-ready)
npx prisma migrate dev --name description_of_change

# Open database GUI
npx prisma studio

# Reset database (WARNING: deletes all data)
npx prisma migrate reset

# View database schema
npx prisma db pull
```

### Adding New Database Models

1. Edit `prisma/schema.prisma`:
```prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  content   String
  userId    String
  user      User     @relation(fields: [userId], references: [id])
  createdAt DateTime @default(now())
  
  @@map("post")
}
```

2. Update User model to include relation:
```prisma
model User {
  // ... existing fields
  posts     Post[]
}
```

3. Push to database:
```bash
npx prisma db push
```

4. Use in your code:
```typescript
import { PrismaClient } from "@/lib/generated/prisma";

const prisma = new PrismaClient();

// Create a post
const post = await prisma.post.create({
  data: {
    title: "Hello World",
    content: "My first post",
    userId: session.user.id,
  },
});
```

## Custom Color System

### Aspect Brand Colors

This project includes a comprehensive color system based on Aspect's brand guidelines, defined in `colors.ts` and integrated with Tailwind CSS.

### Color Configuration

The colors are configured in `app/globals.css` using Tailwind v4's `@theme` directive:

```css
@theme {
  /* Brand Colors */
  --color-brand-blue: #27549d;
  --color-brand-yellow: #f1ff24;

  /* Primary Colors */
  --color-primary: #27549d;
  --color-primary-light: #7099db;
  --color-primary-darker: #17325e;
  --color-primary-subtle: #f7f9fd;

  /* Error Colors */
  --color-error: #d15134;
  --color-error-light: #e49786;
  --color-error-subtle: #faedea;

  /* ... and more */
}
```

### Using Custom Colors

#### In Tailwind Classes

```tsx
// Backgrounds
<div className="bg-brand-blue">Brand blue background</div>
<div className="bg-primary-subtle">Light blue background</div>

// Text
<h1 className="text-grayscale-title">Dark title</h1>
<p className="text-grayscale-body">Body text</p>
<span className="text-error">Error message</span>

// Borders
<div className="border border-border-primary">Primary border</div>
<div className="border-error">Error border</div>

// Hover states
<button className="bg-primary hover:bg-primary-darker">
  Button
</button>
```

#### Color Categories

| Category | Purpose | Example Classes |
|----------|---------|----------------|
| **brand** | Primary brand colors | `bg-brand-blue`, `text-brand-yellow` |
| **primary** | Main UI colors | `bg-primary`, `text-primary-darker` |
| **error** | Error states | `bg-error-subtle`, `text-error` |
| **warning** | Warning states | `bg-warning-subtle`, `text-warning` |
| **support** | Supporting colors | `text-support-green`, `bg-support-gray` |
| **grayscale** | Text hierarchy | `text-grayscale-title`, `text-grayscale-body` |
| **border** | Border colors | `border-border-primary`, `border-grayscale-border` |
| **surface** | Surface backgrounds | `bg-surface-primary`, `bg-surface-error` |

#### Complete Color Reference

```tsx
// Brand Colors
bg-brand-blue           // #27549d
bg-brand-yellow         // #f1ff24

// Primary (Blue variations)
bg-primary              // #27549d (default)
bg-primary-light        // #7099db
bg-primary-darker       // #17325e
bg-primary-subtle       // #f7f9fd (very light)

// Error (Red variations)
bg-error                // #d15134
bg-error-light          // #e49786
bg-error-darker         // #812f1d
bg-error-subtle         // #faedea

// Warning (Orange variations)
bg-warning              // #f29630
bg-warning-light        // #f7c182
bg-warning-darker       // #a35c0a
bg-warning-subtle       // #fef5ec

// Grayscale (Text hierarchy)
text-grayscale-title    // #1a1d23 (headings)
text-grayscale-body     // #323843 (body text)
text-grayscale-subtle   // #646f86 (secondary text)
text-grayscale-caption  // #848ea3 (captions)
text-grayscale-disabled // #cdd1da (disabled state)
```

### Adding Custom Colors

To add your own colors:

1. **Define in `colors.ts`** (optional, for reference):
```typescript
export const colors = {
  custom: {
    purple: "#8B5CF6",
  },
};
```

2. **Add to `app/globals.css`**:
```css
@theme {
  --color-custom-purple: #8B5CF6;
}
```

3. **Use in components**:
```tsx
<div className="bg-custom-purple">Purple background</div>
```

## Project Structure

```
aspect-sales-marketing-forecast-clone/
│
├── app/                          # Next.js App Router
│   ├── api/                      # API Routes
│   │   └── auth/
│   │       └── [...all]/
│   │           └── route.ts      # Better Auth handler
│   │
│   ├── dashboard/                # Protected dashboard page
│   │   └── page.tsx              # Main dashboard (requires auth)
│   │
│   ├── login/                    # Login page
│   │   ├── page.tsx              # Login page layout
│   │   ├── LoginForm.tsx         # OAuth buttons
│   │   ├── MicrosoftIcon.tsx    # Microsoft logo
│   │   └── GithubIcon.tsx       # GitHub logo (if used)
│   │
│   ├── layout.tsx                # Root layout (Navbar + providers)
│   ├── page.tsx                  # Home (redirects to /dashboard)
│   ├── Navbar.tsx                # Navigation with logout
│   ├── globals.css               # Tailwind + custom colors
│   └── favicon.ico               # Site icon
│
├── lib/                          # Utility libraries
│   ├── actions/
│   │   └── auth-actions.ts       # Server actions for auth
│   ├── generated/prisma/         # Generated Prisma Client
│   ├── auth.ts                   # Better Auth server config
│   └── auth-client.ts            # Better Auth client config
│
├── prisma/
│   └── schema.prisma             # Database schema (User, Session, etc.)
│
├── public/
│   └── aspect-logo-primary.svg   # Aspect logo
│
├── colors.ts                     # Color definitions (reference)
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Example env file (safe to commit)
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
├── tailwind.config.ts            # Tailwind configuration (if needed)
└── README.md                     # This file
```

### Key Files Explained

| File | Purpose |
|------|---------|
| `lib/auth.ts` | Server-side Better Auth configuration |
| `lib/auth-client.ts` | Client-side auth utilities (logout, etc.) |
| `lib/actions/auth-actions.ts` | Server actions for OAuth sign-in |
| `app/api/auth/[...all]/route.ts` | Handles all auth API routes |
| `prisma/schema.prisma` | Database schema definition |
| `app/globals.css` | Tailwind configuration + custom colors |
| `colors.ts` | Color reference (not used directly) |

## Deployment

### Deploy to Vercel (Recommended)

Vercel is the easiest way to deploy Next.js applications:

#### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### 2. Import to Vercel

1. Go to [Vercel](https://vercel.com)
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Vercel auto-detects Next.js settings

#### 3. Configure Environment Variables

In Vercel project settings, add:

```
DATABASE_URL=postgresql://...your-neon-production-url...
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=your_tenant_id
GITHUB_CLIENT_ID=your_github_id
GITHUB_CLIENT_SECRET=your_github_secret
NEXT_PUBLIC_BASE_URL=https://your-domain.vercel.app
```

#### 4. Update OAuth Redirect URIs

**Microsoft:**
- Add redirect URI: `https://your-domain.vercel.app/api/auth/callback/microsoft`

**GitHub:**
- Add callback URL: `https://your-domain.vercel.app/api/auth/callback/github`

#### 5. Deploy

Click **"Deploy"** - Vercel will build and deploy automatically!

### Production Checklist

- [ ] Environment variables configured
- [ ] OAuth redirect URIs updated
- [ ] Database connection string uses production Neon database
- [ ] `NEXT_PUBLIC_BASE_URL` set to production domain
- [ ] Test login flow on production
- [ ] Monitor error logs
- [ ] Set up custom domain (optional)

## Troubleshooting

### Common Issues

<details>
<summary><strong>Error: "DATABASE_URL not found"</strong></summary>

**Problem:** Prisma can't find the database connection string.

**Solution:**
1. Check that `.env` exists in the root directory
2. Verify `DATABASE_URL` is set correctly
3. Restart your development server
4. Run `npx prisma generate` again

</details>

<details>
<summary><strong>Error: "Social provider is missing clientId or clientSecret"</strong></summary>

**Problem:** OAuth credentials not configured.

**Solutions:**
1. **Option A**: Add credentials to `.env` (see [OAuth Setup](#5-set-up-oauth-providers))
2. **Option B**: Temporarily disable OAuth in `lib/auth.ts`:
```typescript
export const auth = betterAuth({
  database: prismaAdapter(prisma, { provider: "postgresql" }),
  // socialProviders: { ... }, // Comment out
});
```

</details>

<details>
<summary><strong>Error: "Cannot find module '@/lib/auth-client'"</strong></summary>

**Problem:** TypeScript cache issue.

**Solution:**
1. Restart your IDE
2. Or: Cmd/Ctrl + Shift + P → "TypeScript: Restart TS Server"
3. Or: Delete `.next` folder and restart dev server

</details>

<details>
<summary><strong>OAuth redirect error / 404</strong></summary>

**Problem:** Redirect URI mismatch.

**Solution:**
1. Check callback URL in OAuth provider settings exactly matches:
   - Microsoft: `http://localhost:3000/api/auth/callback/microsoft`
   - GitHub: `http://localhost:3000/api/auth/callback/github`
2. Ensure no trailing slashes
3. Check port number matches your dev server

</details>

<details>
<summary><strong>Database connection timeout</strong></summary>

**Problem:** Can't connect to Neon database.

**Solution:**
1. Check your internet connection
2. Verify the connection string is correct
3. In Neon console, check if database is active
4. Try using the "Pooled connection" URL instead
5. Check if your IP is whitelisted (Neon allows all by default)

</details>

<details>
<summary><strong>Prisma schema error in IDE</strong></summary>

**Problem:** IDE shows error about `url` property in Prisma 7.

**Solution:**
This is a false warning - you're using Prisma 6. Just ignore it or:
```bash
# Suppress the warning
npx prisma validate
```

</details>

### Debug Mode

Enable Better Auth debug logging:

```typescript
// lib/auth.ts
export const auth = betterAuth({
  // ... existing config
  advanced: {
    debug: true, // Add this
  },
});
```

### Get Help

- **Better Auth**: [Documentation](https://better-auth.com) | [Discord](https://discord.gg/better-auth)
- **Prisma**: [Documentation](https://www.prisma.io/docs) | [Discord](https://pris.ly/discord)
- **Next.js**: [Documentation](https://nextjs.org/docs) | [GitHub Discussions](https://github.com/vercel/next.js/discussions)
- **Neon**: [Documentation](https://neon.tech/docs) | [Discord](https://discord.gg/neon)

## Additional Resources

### Learn More

- [Next.js App Router Tutorial](https://nextjs.org/learn)
- [Better Auth Getting Started](https://better-auth.com/docs/getting-started)
- [Prisma Quick Start](https://www.prisma.io/docs/getting-started)
- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)

### Best Practices

- **Security**: Never commit `.env` files, use environment variables
- **Database**: Always use migrations in production (`prisma migrate deploy`)
- **Authentication**: Keep OAuth secrets secure, rotate them periodically
- **Code Quality**: Run `npm run lint` before committing
- **Testing**: Test authentication flow thoroughly before deploying

## License

MIT

---

**Built with ❤️ using Next.js, Better Auth, and Neon PostgreSQL**

Need help? [Open an issue](https://github.com/your-repo/issues) or check the troubleshooting section above.