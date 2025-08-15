import React, { useState } from 'react';
import { motion } from 'framer-motion';
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
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar';
import { Badge } from '../../components/ui/badge';
import { 
  User,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Camera,
  Save,
  Edit,
  Shield,
  Heart
} from 'lucide-react';

const ProfilePage: React.FC = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    firstName: 'Alex',
    lastName: 'Johnson',
    email: 'alex.johnson@example.com',
    phone: '+1 (555) 123-4567',
    dateOfBirth: '1990-05-15',
    address: '123 Health Street, Medical City, MC 12345',
    bloodType: 'O+',
    emergencyContact: 'Sarah Johnson',
    emergencyPhone: '+1 (555) 987-6543'
  });

  const handleInputChange = (field: string, value: string) => {
    setProfileData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    setIsEditing(false);
    // Handle save logic here
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-4xl mx-auto space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
            <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
            <p className="text-gray-600 mt-1">Manage your personal information and preferences</p>
          </div>
          <Button
            onClick={() => setIsEditing(!isEditing)}
            className="bg-primary text-white"
          >
            {isEditing ? (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            ) : (
              <>
                <Edit className="h-4 w-4 mr-2" />
                Edit Profile
              </>
            )}
          </Button>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Picture */}
          <motion.div variants={itemVariants}>
            <Card className="shadow-lg">
              <CardHeader className="text-center">
                <CardTitle>Profile Picture</CardTitle>
              </CardHeader>
              <CardContent className="text-center space-y-4">
                <div className="relative inline-block">
                  <Avatar className="h-32 w-32 mx-auto">
                    <AvatarImage src="/api/placeholder/128/128" />
                    <AvatarFallback className="bg-primary text-white text-2xl">AJ</AvatarFallback>
                  </Avatar>
                  {isEditing && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute bottom-0 right-0 rounded-full h-10 w-10 p-0"
                    >
                      <Camera className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg">{profileData.firstName} {profileData.lastName}</h3>
                  <Badge variant="info">Patient ID: P-1234</Badge>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Personal Information */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Update your personal details and contact information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="firstName"
                        value={profileData.firstName}
                        onChange={(e) => handleInputChange('firstName', e.target.value)}
                        className="pl-10"
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="lastName"
                        value={profileData.lastName}
                        onChange={(e) => handleInputChange('lastName', e.target.value)}
                        className="pl-10"
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
        </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      value={profileData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="pl-10"
                      disabled={!isEditing}
                    />
        </div>
        </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="phone"
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="pl-10"
                      disabled={!isEditing}
                    />
        </div>
        </div>

                <div className="space-y-2">
                  <Label htmlFor="dateOfBirth">Date of Birth</Label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="dateOfBirth"
                      type="date"
                      value={profileData.dateOfBirth}
                      onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                      className="pl-10"
                      disabled={!isEditing}
                    />
        </div>
      </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <textarea
                      id="address"
                      value={profileData.address}
                      onChange={(e) => handleInputChange('address', e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100"
                      rows={3}
                      disabled={!isEditing}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Medical Information */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Medical Information</CardTitle>
              <CardDescription>Important medical details for healthcare providers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="bloodType">Blood Type</Label>
                    <div className="relative">
                      <Heart className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="bloodType"
                        value={profileData.bloodType}
                        onChange={(e) => handleInputChange('bloodType', e.target.value)}
                        className="pl-10"
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="emergencyContact">Emergency Contact</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="emergencyContact"
                        value={profileData.emergencyContact}
                        onChange={(e) => handleInputChange('emergencyContact', e.target.value)}
                        className="pl-10"
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergencyPhone">Emergency Phone</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="emergencyPhone"
                        type="tel"
                        value={profileData.emergencyPhone}
                        onChange={(e) => handleInputChange('emergencyPhone', e.target.value)}
                        className="pl-10"
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Security Settings */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Security & Privacy</CardTitle>
              <CardDescription>Manage your account security and privacy settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="h-5 w-5 text-blue-600" />
                  <div>
                    <h4 className="font-medium">Two-Factor Authentication</h4>
                    <p className="text-sm text-gray-600">Add an extra layer of security to your account</p>
                  </div>
                </div>
                <Button variant="outline">Enable</Button>
              </div>
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Mail className="h-5 w-5 text-green-600" />
                  <div>
                    <h4 className="font-medium">Email Notifications</h4>
                    <p className="text-sm text-gray-600">Receive important updates via email</p>
      </div>
    </div>
                <Button variant="outline">Configure</Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default ProfilePage;






