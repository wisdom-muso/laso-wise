import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { 
  Card as NextUICard,
  CardBody,
  Input as NextUIInput,
  Button as NextUIButton,
  Divider,
  Checkbox,
  Select,
  SelectItem
} from '@nextui-org/react';
import { 
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  Phone,
  Calendar,
  Heart,
  Activity,
  Shield,
  Users,
  ArrowRight,
  Globe,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const RegisterPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userType, setUserType] = useState('patient');
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    userType: 'patient',
    agreeToTerms: false,
    agreeToPrivacy: false
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      // Handle registration logic here
    }, 2000);
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  const benefits = [
    { icon: Heart, title: 'Personalized Care', description: 'Get tailored health recommendations' },
    { icon: Activity, title: 'Health Tracking', description: 'Monitor your vital signs and progress' },
    { icon: Shield, title: 'Secure Platform', description: 'Your data is protected with encryption' },
    { icon: Users, title: 'Expert Access', description: 'Connect with healthcare professionals' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left Side - Benefits */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="hidden lg:block"
        >
          <motion.div variants={itemVariants} className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-teal-500 rounded-xl flex items-center justify-center">
                <Globe className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900">LASO Health</h1>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">
              Join the Future of Healthcare
            </h2>
            <p className="text-gray-600 text-lg">
              Create your account and start your journey towards better health with our comprehensive digital platform.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-6">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                variants={itemVariants}
                whileHover={{ scale: 1.02 }}
                className="flex items-start space-x-4 p-4 rounded-xl bg-white/50 backdrop-blur-sm border border-white/20"
              >
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-teal-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <benefit.icon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">{benefit.title}</h3>
                  <p className="text-gray-600 text-sm">{benefit.description}</p>
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div variants={itemVariants} className="mt-8 p-6 bg-gradient-to-r from-blue-500 to-teal-500 rounded-xl text-white">
            <h3 className="font-semibold mb-2">Already have an account?</h3>
            <p className="text-blue-100 text-sm mb-4">
              Sign in to access your health dashboard and continue your care journey.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center text-blue-100 hover:text-white transition-colors"
            >
              Sign in to your account
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </motion.div>
        </motion.div>

        {/* Right Side - Registration Form */}
        <motion.div
          variants={itemVariants}
          initial="hidden"
          animate="visible"
          className="flex justify-center"
        >
          <NextUICard className="w-full max-w-md shadow-2xl">
            <CardHeader className="text-center pb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="h-8 w-8 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">
                Create Account
              </CardTitle>
              <CardDescription className="text-gray-600">
                Join LASO Health and start your health journey
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* User Type Selection */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    I am a
                  </Label>
                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      type="button"
                      variant={userType === 'patient' ? 'default' : 'outline'}
                      className={`h-12 ${userType === 'patient' ? 'bg-primary text-white' : ''}`}
                      onClick={() => setUserType('patient')}
                    >
                      <User className="h-4 w-4 mr-2" />
                      Patient
                    </Button>
                    <Button
                      type="button"
                      variant={userType === 'doctor' ? 'default' : 'outline'}
                      className={`h-12 ${userType === 'doctor' ? 'bg-primary text-white' : ''}`}
                      onClick={() => setUserType('doctor')}
                    >
                      <Shield className="h-4 w-4 mr-2" />
                      Doctor
                    </Button>
                  </div>
                </div>

                {/* Name Fields */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName" className="text-sm font-medium text-gray-700">
                      First Name
                    </Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="firstName"
                        type="text"
                        placeholder="First name"
                        value={formData.firstName}
                        onChange={(e) => handleInputChange('firstName', e.target.value)}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-sm font-medium text-gray-700">
                      Last Name
                    </Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="lastName"
                        type="text"
                        placeholder="Last name"
                        value={formData.lastName}
                        onChange={(e) => handleInputChange('lastName', e.target.value)}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Email Address
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                {/* Phone */}
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-sm font-medium text-gray-700">
                    Phone Number
                  </Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="Enter your phone number"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a password"
                      value={formData.password}
                      onChange={(e) => handleInputChange('password', e.target.value)}
                      className="pl-10 pr-10"
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
      </div>

                {/* Confirm Password */}
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                    Confirm Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Confirm your password"
                      value={formData.confirmPassword}
                      onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                      className="pl-10 pr-10"
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
        </div>
          </div>

                {/* Terms and Privacy */}
                <div className="space-y-3">
                  <div className="flex items-start space-x-2">
                    <Checkbox
                      isSelected={formData.agreeToTerms}
                      onValueChange={(value) => handleInputChange('agreeToTerms', value)}
                    >
                      <span className="text-sm text-gray-700">
                        I agree to the{' '}
                        <Link to="/terms" className="text-blue-600 hover:text-blue-500">
                          Terms of Service
                        </Link>
                      </span>
                    </Checkbox>
          </div>
                  <div className="flex items-start space-x-2">
                    <Checkbox
                      isSelected={formData.agreeToPrivacy}
                      onValueChange={(value) => handleInputChange('agreeToPrivacy', value)}
                    >
                      <span className="text-sm text-gray-700">
                        I agree to the{' '}
                        <Link to="/privacy" className="text-blue-600 hover:text-blue-500">
                          Privacy Policy
                        </Link>
                      </span>
                    </Checkbox>
          </div>
          </div>

                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-500 to-teal-500 text-white py-3 rounded-lg font-medium hover:from-blue-600 hover:to-teal-600 transition-all duration-200"
                  disabled={isLoading || !formData.agreeToTerms || !formData.agreeToPrivacy}
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Creating account...</span>
          </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <span>Create Account</span>
                      <ArrowRight className="h-4 w-4" />
            </div>
          )}
                </Button>

                <Divider className="my-6" />

                <div className="text-center">
                  <p className="text-gray-600 text-sm">
                    Already have an account?{' '}
                    <Link
                      to="/login"
                      className="text-blue-600 hover:text-blue-500 font-medium transition-colors"
                    >
                      Sign in
                    </Link>
                  </p>
                </div>
              </form>
            </CardContent>
          </NextUICard>
        </motion.div>
        </div>
    </div>
  );
};

export default RegisterPage;


