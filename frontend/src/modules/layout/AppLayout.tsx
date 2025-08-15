import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle 
} from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar';
import { Badge } from '../../components/ui/badge';
import { 
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  DropdownContent,
  Switch,
  User,
  Chip
} from '@nextui-org/react';
import { 
  Home,
  FileText,
  FolderOpen,
  Calendar,
  Truck,
  Globe,
  Settings,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  Menu,
  X,
  Activity,
  Heart,
  Shield,
  Users,
  BarChart3
} from 'lucide-react';

const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const location = useLocation();

  const navigationItems = [
    { 
      name: 'My Health Dashboard', 
      icon: Home, 
      path: '/patients/dashboard',
      active: location.pathname === '/patients/dashboard' || location.pathname === '/'
    },
    { 
      name: 'Risk Reports', 
      icon: FileText, 
      path: '/patients/risk-reports',
      active: location.pathname === '/patients/risk-reports'
    },
    { 
      name: 'Medical Records', 
      icon: FolderOpen, 
      path: '/patients/medical-records',
      active: location.pathname === '/patients/medical-records'
    },
    { 
      name: 'Appointments', 
      icon: Calendar, 
      path: '/patients/appointments',
      active: location.pathname === '/patients/appointments'
    },
    { 
      name: 'Mobile Clinic', 
      icon: Truck, 
      path: '/mobile-clinic',
      active: location.pathname === '/mobile-clinic'
    },
    { 
      name: 'Laso Connect', 
      icon: Globe, 
      path: '/laso-connect',
      active: location.pathname === '/laso-connect'
    },
    { 
      name: 'Settings', 
      icon: Settings, 
      path: '/patients/settings',
      active: location.pathname === '/patients/settings'
    }
  ];

  const sidebarVariants = {
    open: { x: 0, opacity: 1 },
    closed: { x: '-100%', opacity: 0 }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        variants={sidebarVariants}
        initial="closed"
        animate={sidebarOpen ? "open" : "closed"}
        className={`fixed left-0 top-0 z-50 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">L</span>
              </div>
              <span className="text-xl font-bold text-gray-900">LASQ</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigationItems.map((item) => (
              <motion.div
                key={item.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Link
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    item.active
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
          </Link>
              </motion.div>
            ))}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src="/api/placeholder/40/40" />
                <AvatarFallback className="bg-primary text-white">AJ</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">Alex Johnson</p>
                <p className="text-xs text-gray-500">Patient ID: P-1234</p>
              </div>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-6 py-4">
            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>

            {/* Title */}
            <h1 className="text-xl font-semibold text-gray-900 lg:ml-0">
              Patient Health Portal
            </h1>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-4">
              {/* Language/Region */}
              <Button variant="ghost" size="sm">
                <Globe className="h-4 w-4" />
              </Button>

              {/* Notifications */}
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-4 w-4" />
                <Badge 
                  variant="danger" 
                  className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
                >
                  3
                </Badge>
              </Button>

              {/* Theme Toggle */}
              <Switch
                size="sm"
                color="primary"
                startContent={<Sun className="h-4 w-4" />}
                endContent={<Moon className="h-4 w-4" />}
                isSelected={isDark}
                onValueChange={setIsDark}
              />

              {/* User Dropdown */}
              <Dropdown placement="bottom-end">
                <DropdownTrigger>
                  <Button
                    variant="ghost"
                    className="flex items-center space-x-2"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/api/placeholder/32/32" />
                      <AvatarFallback className="bg-primary text-white text-xs">AJ</AvatarFallback>
                    </Avatar>
                    <div className="hidden md:block text-left">
                      <p className="text-sm font-medium">Alex Johnson</p>
                      <p className="text-xs text-gray-500">Patient ID: P-1234</p>
                    </div>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownTrigger>
                <DropdownContent aria-label="User actions">
                  <DropdownItem key="profile">Profile Settings</DropdownItem>
                  <DropdownItem key="preferences">Preferences</DropdownItem>
                  <DropdownItem key="help">Help & Support</DropdownItem>
                  <DropdownItem key="logout" color="danger">
                    Sign Out
                  </DropdownItem>
                </DropdownContent>
              </Dropdown>
            </div>
        </div>
      </header>

        {/* Page Content */}
        <main className="p-6">
        <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;



