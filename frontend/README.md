# LASO Health - Modern React Frontend

A beautiful, modern React frontend for the LASO Digital Health platform, built with NextUI, shadcn/ui, and Framer Motion animations.

## 🚀 Features

- **Modern UI/UX**: Beautiful, responsive design with smooth animations
- **NextUI Components**: Professional UI components with excellent accessibility
- **shadcn/ui**: High-quality, customizable component library
- **Framer Motion**: Smooth, performant animations
- **TypeScript**: Full type safety and better developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid development
- **React Query**: Powerful data fetching and caching
- **React Router**: Client-side routing
- **Lucide Icons**: Beautiful, customizable icons

## 🎨 Design Inspiration

This frontend is inspired by modern healthcare applications with:
- Clean, medical-grade design
- Accessible color schemes
- Intuitive navigation
- Responsive layouts
- Beautiful animations and transitions

## 📦 Installation

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

4. **Preview Production Build**
   ```bash
   npm run preview
   ```

## 🛠️ Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **NextUI** - Component library
- **shadcn/ui** - Component primitives
- **Framer Motion** - Animations
- **React Query** - Data fetching
- **React Router** - Routing
- **Lucide React** - Icons

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/           # shadcn/ui components
│   ├── modules/
│   │   ├── auth/         # Authentication pages
│   │   ├── patient/      # Patient dashboard
│   │   ├── doctor/       # Doctor dashboard
│   │   └── layout/       # Layout components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utility functions
│   └── styles/           # Global styles
├── public/               # Static assets
└── package.json
```

## 🎯 Key Components

### Patient Dashboard
- Health assessment overview
- Medication reminders
- Health recommendations
- Next appointment details
- Quick actions

### Doctor Dashboard
- Patient statistics
- Appointment management
- Recent patients
- Quick actions
- Analytics overview

### Authentication
- Modern login/register forms
- Beautiful animations
- Form validation
- Responsive design

## 🎨 Design System

### Colors
- **Primary**: Teal/Blue gradient (#14b8a6 to #3b82f6)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Danger**: Red (#ef4444)
- **Info**: Blue (#3b82f6)

### Typography
- **Font**: Inter (system fallback)
- **Headings**: Bold, large scale
- **Body**: Regular, readable

### Animations
- **Fade In**: Smooth opacity transitions
- **Slide Up**: Vertical entrance animations
- **Scale**: Interactive hover effects
- **Stagger**: Sequential element animations

## 🔧 Configuration

### Tailwind Config
The project uses a custom Tailwind configuration with:
- NextUI plugin integration
- Custom color palette
- Animation keyframes
- Responsive breakpoints

### NextUI Theme
Custom NextUI theme with:
- Light and dark mode support
- Custom color schemes
- Consistent spacing
- Professional styling

## 📱 Responsive Design

The application is fully responsive with:
- Mobile-first approach
- Tablet optimizations
- Desktop enhancements
- Touch-friendly interactions

## 🚀 Performance

- **Code Splitting**: Automatic route-based splitting
- **Lazy Loading**: Components loaded on demand
- **Optimized Images**: WebP format with fallbacks
- **Minimal Bundle**: Tree-shaking and optimization

## 🔒 Security

- **CSRF Protection**: Built-in CSRF token handling
- **Input Validation**: Form validation and sanitization
- **Secure Headers**: Security headers configuration
- **HTTPS Only**: Production HTTPS enforcement

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

## 📦 Deployment

### Vercel (Recommended)
1. Connect your GitHub repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Deploy

### Netlify
1. Connect your repository
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Deploy

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code examples

## 🔄 Updates

To update dependencies:
```bash
npm update
npm audit fix
```

## 📈 Analytics

The application includes:
- Performance monitoring
- User analytics
- Error tracking
- Health checks

---

Built with ❤️ for better healthcare experiences
