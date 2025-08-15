import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Clock, 
  Users, 
  Video, 
  Mic, 
  MicOff, 
  VideoOff, 
  Settings,
  Bell,
  BellOff,
  Monitor,
  Smartphone,
  Wifi,
  WifiOff,
  Heart,
  AlertCircle,
  CheckCircle,
  Camera,
  Volume2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { useAuth } from '../../hooks/useAuth';
import { useConsultations } from '../../hooks/useConsultations';
import { api, endpoints } from '../../lib/api';
import { cn, formatTime } from '../../lib/utils';
import toast from 'react-hot-toast';

interface WaitingRoomProps {
  consultationId?: string;
}

interface QueuePosition {
  position: number;
  estimatedWaitTime: number;
  totalInQueue: number;
}

interface SystemCheck {
  camera: boolean;
  microphone: boolean;
  speakers: boolean;
  internet: boolean;
  browser: boolean;
}

interface PatientComfortFeature {
  id: string;
  title: string;
  description: string;
  enabled: boolean;
}

const WaitingRoom: React.FC<WaitingRoomProps> = ({ consultationId: propConsultationId }) => {
  const { consultationId: paramConsultationId } = useParams<{ consultationId: string }>();
  const consultationId = propConsultationId || paramConsultationId;
  const navigate = useNavigate();
  const { user } = useAuth();
  const { 
    currentConsultation, 
    joinWaitingRoom, 
    isConnected,
    sendMessage 
  } = useConsultations();

  // State management
  const [queuePosition, setQueuePosition] = useState<QueuePosition | null>(null);
  const [waitingTime, setWaitingTime] = useState(0);
  const [systemChecks, setSystemChecks] = useState<SystemCheck>({
    camera: false,
    microphone: false,
    speakers: false,
    internet: false,
    browser: true
  });
  const [mediaPermissions, setMediaPermissions] = useState({
    camera: false,
    microphone: false
  });
  const [previewStream, setPreviewStream] = useState<MediaStream | null>(null);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [comfortFeatures, setComfortFeatures] = useState<PatientComfortFeature[]>([
    { id: 'music', title: 'Relaxing Music', description: 'Calming background music', enabled: false },
    { id: 'breathing', title: 'Breathing Exercise', description: 'Guided breathing to reduce anxiety', enabled: false },
    { id: 'info', title: 'Health Tips', description: 'Educational content while you wait', enabled: false }
  ]);

  // Refs
  const videoPreviewRef = useRef<HTMLVideoElement>(null);
  const waitingTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (consultationId) {
      initializeWaitingRoom();
    }

    return () => {
      cleanup();
    };
  }, [consultationId]);

  useEffect(() => {
    // Start waiting timer
    waitingTimerRef.current = setInterval(() => {
      setWaitingTime(prev => prev + 1);
    }, 1000);

    return () => {
      if (waitingTimerRef.current) {
        clearInterval(waitingTimerRef.current);
      }
    };
  }, []);

  const initializeWaitingRoom = async () => {
    try {
      // Join waiting room
      await joinWaitingRoom(consultationId);
      
      // Check system requirements
      await performSystemChecks();
      
      // Request media permissions
      await requestMediaPermissions();
      
      // Fetch queue position
      await fetchQueuePosition();
      
      // Request notification permission
      if ('Notification' in window && Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        setNotificationsEnabled(permission === 'granted');
      }
      
    } catch (error) {
      console.error('Failed to initialize waiting room:', error);
      toast.error('Failed to join waiting room');
    }
  };

  const performSystemChecks = async () => {
    const checks: Partial<SystemCheck> = {};

    // Check internet connection
    checks.internet = navigator.onLine;

    // Check browser compatibility
    checks.browser = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

    // Check for WebRTC support
    if (window.RTCPeerConnection) {
      checks.browser = true;
    }

    setSystemChecks(prev => ({ ...prev, ...checks }));
  };

  const requestMediaPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });

      setPreviewStream(stream);
      setMediaPermissions({ camera: true, microphone: true });

      // Update system checks
      setSystemChecks(prev => ({
        ...prev,
        camera: true,
        microphone: true,
        speakers: true // Assume speakers work if audio permission granted
      }));

      // Set up video preview
      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream;
      }

    } catch (error) {
      console.error('Media permissions denied:', error);
      setMediaPermissions({ camera: false, microphone: false });
      toast.error('Camera and microphone access required for consultation');
    }
  };

  const fetchQueuePosition = async () => {
    try {
      const response = await api.get(endpoints.telemedicine.queuePosition(consultationId));
      setQueuePosition(response.data);
    } catch (error) {
      console.error('Failed to fetch queue position:', error);
    }
  };

  const toggleMediaDevice = (device: 'audio' | 'video') => {
    if (!previewStream) return;

    const tracks = device === 'audio' 
      ? previewStream.getAudioTracks() 
      : previewStream.getVideoTracks();

    tracks.forEach(track => {
      track.enabled = !track.enabled;
    });

    if (device === 'audio') {
      setAudioEnabled(!audioEnabled);
    } else {
      setVideoEnabled(!videoEnabled);
    }
  };

  const toggleComfortFeature = (featureId: string) => {
    setComfortFeatures(prev => 
      prev.map(feature => 
        feature.id === featureId 
          ? { ...feature, enabled: !feature.enabled }
          : feature
      )
    );
  };

  const testAudioOutput = () => {
    const audio = new Audio('/audio/test-sound.mp3');
    audio.play().catch(() => {
      toast.error('Unable to play test sound. Please check your speakers.');
    });
  };

  const sendMessage = (message: string) => {
    // Send message through WebSocket
    if (isConnected) {
      sendMessage(consultationId, message);
    }
  };

  const cleanup = () => {
    if (previewStream) {
      previewStream.getTracks().forEach(track => track.stop());
    }
    if (waitingTimerRef.current) {
      clearInterval(waitingTimerRef.current);
    }
  };

  const formatWaitingTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getSystemStatus = (): 'good' | 'warning' | 'error' => {
    const checks = Object.values(systemChecks);
    const passed = checks.filter(Boolean).length;
    
    if (passed === checks.length) return 'good';
    if (passed >= checks.length * 0.7) return 'warning';
    return 'error';
  };

  const systemStatus = getSystemStatus();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Virtual Waiting Room
          </h1>
          <p className="text-gray-600">
            Please wait while we prepare your consultation
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Queue Status & System Checks */}
          <div className="space-y-6">
            {/* Queue Position */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Queue Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                {queuePosition ? (
                  <div className="space-y-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        #{queuePosition.position}
                      </div>
                      <p className="text-sm text-gray-600">Your position in queue</p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Estimated wait time:</span>
                        <span className="font-medium">
                          {formatTime(queuePosition.estimatedWaitTime)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>People ahead:</span>
                        <span className="font-medium">{queuePosition.position - 1}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Total in queue:</span>
                        <span className="font-medium">{queuePosition.totalInQueue}</span>
                      </div>
                    </div>

                    <Progress 
                      value={((queuePosition.totalInQueue - queuePosition.position + 1) / queuePosition.totalInQueue) * 100} 
                      className="w-full"
                    />
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <div className="animate-pulse">
                      <div className="text-xl text-gray-500">Loading queue status...</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Waiting Time */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Waiting Time
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-2xl font-mono font-bold text-gray-900">
                    {formatWaitingTime(waitingTime)}
                  </div>
                  <p className="text-sm text-gray-600">Time in waiting room</p>
                </div>
              </CardContent>
            </Card>

            {/* System Checks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  System Status
                  <Badge 
                    variant={systemStatus === 'good' ? 'default' : 
                            systemStatus === 'warning' ? 'secondary' : 'destructive'}
                  >
                    {systemStatus === 'good' ? 'All Good' : 
                     systemStatus === 'warning' ? 'Some Issues' : 'Needs Attention'}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Camera className="h-4 w-4" />
                      <span className="text-sm">Camera</span>
                    </div>
                    {systemChecks.camera ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mic className="h-4 w-4" />
                      <span className="text-sm">Microphone</span>
                    </div>
                    {systemChecks.microphone ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4" />
                      <span className="text-sm">Speakers</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {systemChecks.speakers ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={testAudioOutput}
                        className="ml-1 p-1 h-6"
                      >
                        Test
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {systemChecks.internet ? (
                        <Wifi className="h-4 w-4" />
                      ) : (
                        <WifiOff className="h-4 w-4" />
                      )}
                      <span className="text-sm">Internet</span>
                    </div>
                    {systemChecks.internet ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="h-4 w-4" />
                      <span className="text-sm">Browser</span>
                    </div>
                    {systemChecks.browser ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Center Column - Video Preview & Controls */}
          <div className="space-y-6">
            {/* Video Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Video Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <video
                    ref={videoPreviewRef}
                    autoPlay
                    muted
                    playsInline
                    className={cn(
                      "w-full h-64 bg-gray-900 rounded-lg object-cover",
                      !videoEnabled && "hidden"
                    )}
                  />
                  {!videoEnabled && (
                    <div className="w-full h-64 bg-gray-900 rounded-lg flex items-center justify-center">
                      <VideoOff className="h-12 w-12 text-gray-400" />
                    </div>
                  )}
                  
                  {/* Media Controls */}
                  <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
                    <div className="flex items-center gap-2 bg-black bg-opacity-50 rounded-full p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleMediaDevice('audio')}
                        className={cn(
                          "rounded-full p-2 h-10 w-10",
                          audioEnabled ? "text-white hover:bg-white/20" : "text-red-400 bg-red-500/20"
                        )}
                      >
                        {audioEnabled ? (
                          <Mic className="h-4 w-4" />
                        ) : (
                          <MicOff className="h-4 w-4" />
                        )}
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleMediaDevice('video')}
                        className={cn(
                          "rounded-full p-2 h-10 w-10",
                          videoEnabled ? "text-white hover:bg-white/20" : "text-red-400 bg-red-500/20"
                        )}
                      >
                        {videoEnabled ? (
                          <Video className="h-4 w-4" />
                        ) : (
                          <VideoOff className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Consultation Info */}
            {currentConsultation && (
              <Card>
                <CardHeader>
                  <CardTitle>Consultation Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-600">Doctor:</span>
                      <span className="ml-2 font-medium">
                        Dr. {currentConsultation.doctor?.name}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Scheduled:</span>
                      <span className="ml-2 font-medium">
                        {formatTime(currentConsultation.scheduled_start)}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Type:</span>
                      <span className="ml-2 font-medium">
                        {currentConsultation.consultation_type}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Comfort Features & Settings */}
          <div className="space-y-6">
            {/* Patient Comfort */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="h-5 w-5" />
                  Comfort Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {comfortFeatures.map(feature => (
                    <div key={feature.id} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm">{feature.title}</div>
                        <div className="text-xs text-gray-600">{feature.description}</div>
                      </div>
                      <Button
                        variant={feature.enabled ? "default" : "outline"}
                        size="sm"
                        onClick={() => toggleComfortFeature(feature.id)}
                      >
                        {feature.enabled ? 'On' : 'Off'}
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {notificationsEnabled ? (
                    <Bell className="h-5 w-5" />
                  ) : (
                    <BellOff className="h-5 w-5" />
                  )}
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Browser notifications</span>
                    <Button
                      variant={notificationsEnabled ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotificationsEnabled(!notificationsEnabled)}
                    >
                      {notificationsEnabled ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <p className="text-xs text-gray-600">
                    Get notified when your consultation is ready to start
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Help & Tips */}
            <Card>
              <CardHeader>
                <CardTitle>Pre-Consultation Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div>• Ensure good lighting on your face</div>
                  <div>• Use a quiet environment</div>
                  <div>• Have your medical history ready</div>
                  <div>• Prepare any questions you have</div>
                  <div>• Keep your insurance card handy</div>
                </div>
              </CardContent>
            </Card>

            {/* Emergency Options */}
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="text-red-600">Need Immediate Help?</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button 
                    variant="destructive" 
                    className="w-full"
                    onClick={() => window.open('tel:911')}
                  >
                    Emergency: Call 911
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => navigate('/support')}
                  >
                    Technical Support
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* System Issues Alert */}
        {systemStatus === 'error' && (
          <Alert className="mt-6 border-red-200">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              There are system issues that may affect your consultation quality. 
              Please check your camera, microphone, and internet connection.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default WaitingRoom;