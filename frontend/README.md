# Smart Building Management System (SBMS)

A professional, academic ERP-style platform for managing campus infrastructure complaints. Built with Next.js 16, TypeScript, and TailwindCSS for a clean, institutional interface.

## 🎯 Overview

SBMS is a comprehensive complaint management system designed for college campuses to:
- **Report Issues**: Students easily report infrastructure problems with details and photos
- **AI-Powered Classification**: Automatic categorization and priority assignment
- **Real-time Tracking**: Monitor complaint status throughout resolution
- **Role-Based Dashboards**: Separate interfaces for students, maintenance staff, and administrators
- **Maintenance Analytics**: Detailed reporting and performance metrics

## 🏗️ Project Structure

```
app/
├── page.tsx                          # Landing page
├── login/page.tsx                   # Login page
├── register/page.tsx                # Registration page
├── dashboard/
│   ├── layout.tsx                   # Dashboard layout with sidebar
│   ├── student/
│   │   ├── page.tsx                 # Student dashboard
│   │   ├── report/page.tsx          # Report complaint form
│   │   ├── complaints/page.tsx      # View all complaints
│   │   ├── notifications/page.tsx   # Notifications
│   │   └── profile/page.tsx         # User profile
│   ├── staff/
│   │   ├── page.tsx                 # Staff dashboard
│   │   ├── complaints/page.tsx      # Assigned tasks
│   │   ├── notifications/page.tsx   # Notifications
│   │   └── profile/page.tsx         # Staff profile
│   └── admin/
│       ├── page.tsx                 # Admin dashboard
│       ├── buildings/page.tsx       # Buildings management
│       ├── complaints/page.tsx      # All complaints
│       ├── escalations/page.tsx     # Critical escalations
│       └── staff/page.tsx           # Staff management
├── globals.css                      # Global styles & design tokens
└── layout.tsx                       # Root layout

public/
├── college-1.jpg                    # Campus building image
├── college-2.jpg                    # Campus facility image
├── college-3.jpg                    # Campus entrance image
└── college-4.jpg                    # Campus auditorium image
```

## 🎨 Design System

### Color Palette
- **Background**: Dark Navy (#111827)
- **Foreground**: Off-white (#F3F4F6)
- **Primary**: Blue (#3B82F6)
- **Secondary**: Gray (#6B7280)
- **Accent**: Cyan (#0EA5E9)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Danger**: Red (#EF4444)

### Typography
- **Font Family**: Geist (sans-serif)
- **Mono Font**: Geist Mono

### Components
- Uses shadcn/ui components for consistency
- Responsive design (mobile-first approach)
- Dark theme suitable for institutional platforms
- Minimal animations for professional appearance

## 📱 Features by Role

### Student Dashboard
- View personal complaint statistics
- Submit new complaints with image uploads
- Track complaint status in real-time
- Receive notifications on updates
- View complaint history

### Staff Dashboard
- View assigned maintenance tasks
- Update task status
- Track completion metrics
- Receive task assignments
- Manage work schedule

### Admin Dashboard
- System-wide statistics and analytics
- Manage all buildings and facilities
- View all complaints across campus
- Escalate critical issues
- Manage staff assignments
- Generate reports

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- pnpm (package manager)

### Installation

1. **Clone or download the project**
   ```bash
   cd v0-project
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Set up environment variables** (optional for backend integration)
   Create a `.env.local` file:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run development server**
   ```bash
   pnpm dev
   ```

5. **Open in browser**
   ```
   http://localhost:3000
   ```

## 📋 Available Routes

### Public Routes
- `/` - Landing page
- `/login` - Login page
- `/register` - Registration page

### Protected Routes (Dashboard)
- `/dashboard/student` - Student home
- `/dashboard/student/report` - Report issue
- `/dashboard/student/complaints` - My complaints
- `/dashboard/student/notifications` - Notifications
- `/dashboard/student/profile` - User profile

- `/dashboard/staff` - Staff home
- `/dashboard/staff/complaints` - Assigned tasks
- `/dashboard/staff/notifications` - Notifications
- `/dashboard/staff/profile` - Staff profile

- `/dashboard/admin` - Admin home
- `/dashboard/admin/buildings` - Buildings management
- `/dashboard/admin/complaints` - All complaints
- `/dashboard/admin/escalations` - Critical issues
- `/dashboard/admin/staff` - Staff management

## 🔧 Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **Package Manager**: pnpm

## 🎓 Customization

### Update College Information
1. Edit the college name/details in `/app/page.tsx` (landing page)
2. Update building names in `/app/dashboard/admin/buildings/page.tsx`
3. Modify your college logo in the sidebar (replace icon)

### Change Colors
Edit design tokens in `/app/globals.css`:
```css
:root {
  --primary: 59 130 246;  /* Blue */
  --accent: 14 165 233;   /* Cyan */
  /* ... more colors */
}
```

### Add Your College Images
1. Replace the college images in `/public/` directory
2. Images are used in:
   - Landing page hero section
   - Login/Register pages
   - Gallery section

## 📡 Backend Integration

This frontend is designed to connect with a FastAPI/Django backend. To integrate:

1. **Update API client** in `/lib/api.ts` (when created)
2. **Add environment variables** for API endpoints
3. **Implement authentication** using the auth endpoints
4. **Connect real data** by replacing mock data with API calls

### Expected API Endpoints

```
POST   /auth/register          - User registration
POST   /auth/login             - User login
GET    /auth/me                - Get current user
POST   /auth/logout            - User logout

GET    /buildings              - List all buildings
POST   /buildings              - Create building
PUT    /buildings/{id}         - Update building
DELETE /buildings/{id}         - Delete building

GET    /complaints             - Get user complaints
GET    /complaints/all         - Get all complaints (admin)
GET    /complaints/assigned    - Get assigned complaints (staff)
POST   /complaints             - Create complaint
PUT    /complaints/{id}/status - Update status
PUT    /complaints/{id}/assign - Assign complaint

GET    /notifications          - Get notifications
PUT    /notifications/{id}/read - Mark as read
```

## 🔐 Security Considerations

- Implement JWT token authentication
- Use HTTPS in production
- Validate all form inputs
- Implement role-based access control (RBAC)
- Use secure cookies for session management
- Add CSRF protection
- Implement rate limiting on API

## 📈 Future Enhancements

- [ ] Real-time WebSocket notifications
- [ ] Advanced analytics and reporting
- [ ] Calendar integration for scheduling
- [ ] Email notifications
- [ ] Mobile app (React Native)
- [ ] Complaint history export
- [ ] SLA tracking and alerts
- [ ] Integration with maintenance software
- [ ] Multi-language support
- [ ] Accessibility improvements

## 📝 License

This project is part of a college infrastructure management system.

## 👥 Support

For issues or questions, contact your system administrator.

---

**Built with ❤️ for campus excellence**
