import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Video, VideoOff, Mic, MicOff, Phone, PhoneOff, 
  MessageCircle, Users, Settings, AlertTriangle,
  Monitor, MoreVertical, Camera, Volume2, VolumeX
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger 
} from '../../components/ui/dialog';
import { useConsultations, type Consultation } from '../../hooks/useConsultations';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';

interface ConsultationRoomProps {
  consultation: Consultation;
}

const ConsultationRoom: React.FC<ConsultationRoomProps> = ({ consultation }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const {
    messages,
    isConnected,
    participants,
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
    startConsultation,
    endConsultation,
    sendMessage,
    joinWaitingRoom,
    reportTechnicalIssue,
  } = useConsultations();

  // Local state
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [showTechnicalIssueDialog, setShowTechnicalIssueDialog] = useState(false);
  const [technicalIssue, setTechnicalIssue] = useState({
    issue_type: '',
    description: '',
    severity: 'medium'
  });

  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    if (consultation.id) {
      connectWebSocket(consultation.id);
    }

    return () => {
      disconnectWebSocket();
    };
  }, [consultation.id, connectWebSocket, disconnectWebSocket]);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize video based on provider
  useEffect(() => {
    initializeVideo();
  }, [consultation.video_provider]);

  const initializeVideo = async () => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: isVideoEnabled,
        audio: isAudioEnabled
      });

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Initialize video provider integration
      switch (consultation.video_provider) {
        case 'jitsi':
          await initializeJitsi();
          break;
        case 'zoom':
          await initializeZoom();
          break;
        case 'google_meet':
          await initializeGoogleMeet();
          break;
        default:
          console.warn('Unknown video provider:', consultation.video_provider);
      }
    } catch (error) {
      console.error('Error initializing video:', error);
      toast.error('Failed to access camera/microphone');
    }
  };

  const initializeJitsi = async () => {
    // Load Jitsi Meet API
    if (!(window as any).JitsiMeetJS) {
      const script = document.createElement('script');
      script.src = 'https://meet.jit.si/external_api.js';
      document.head.appendChild(script);
      
      await new Promise((resolve) => {
        script.onload = resolve;
      });
    }

    // Initialize Jitsi Meet
    const domain = 'meet.jit.si';
    const options = {
      roomName: consultation.meeting_id,
      width: '100%',
      height: 400,
      parentNode: document.getElementById('jitsi-container'),
      configOverwrite: {
        startWithAudioMuted: !isAudioEnabled,
        startWithVideoMuted: !isVideoEnabled,
      },
      interfaceConfigOverwrite: {
        TOOLBAR_BUTTONS: [
          'microphone', 'camera', 'closedcaptions', 'desktop', 'fullscreen',
          'fodeviceselection', 'hangup', 'profile', 'recording',
          'livestreaming', 'etherpad', 'sharedvideo', 'settings', 'raisehand',
          'videoquality', 'filmstrip', 'invite', 'feedback', 'stats', 'shortcuts'
        ],
      }
    };

    const api = new (window as any).JitsiMeetExternalAPI(domain, options);

    // Event listeners
    api.addEventListener('participantJoined', (participant: any) => {
      console.log('Participant joined:', participant);
    });

    api.addEventListener('participantLeft', (participant: any) => {
      console.log('Participant left:', participant);
    });

    api.addEventListener('videoConferenceJoined', () => {
      console.log('Conference joined');
    });
  };

  const initializeZoom = async () => {
    // Zoom integration would require Zoom Web SDK
    console.log('Zoom integration not implemented in this demo');
    toast.info('Redirecting to Zoom meeting...');
    window.open(consultation.meeting_url, '_blank');
  };

  const initializeGoogleMeet = async () => {
    // Google Meet integration would require Google Meet API
    console.log('Google Meet integration not implemented in this demo');
    toast.info('Redirecting to Google Meet...');
    window.open(consultation.meeting_url, '_blank');
  };

  const handleStartConsultation = async () => {
    if (user?.role !== 'doctor') {
      toast.error('Only doctors can start consultations');
      return;
    }

    try {
      await startConsultation(consultation.id);
    } catch (error) {
      console.error('Failed to start consultation:', error);
    }
  };

  const handleEndConsultation = async () => {
    if (user?.role !== 'doctor') {
      toast.error('Only doctors can end consultations');
      return;
    }

    try {
      await endConsultation(consultation.id);
      navigate('/consultations');
    } catch (error) {
      console.error('Failed to end consultation:', error);
    }
  };

  const handleJoinWaitingRoom = async () => {
    if (user?.role !== 'patient') {
      toast.error('Only patients can join the waiting room');
      return;
    }

    try {
      await joinWaitingRoom(consultation.id);
    } catch (error) {
      console.error('Failed to join waiting room:', error);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    try {
      await sendMessage(consultation.id, chatMessage);
      setChatMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleReportIssue = async () => {
    try {
      await reportTechnicalIssue(consultation.id, technicalIssue);
      setShowTechnicalIssueDialog(false);
      setTechnicalIssue({ issue_type: '', description: '', severity: 'medium' });
    } catch (error) {
      console.error('Failed to report issue:', error);
    }
  };

  const toggleVideo = () => {
    setIsVideoEnabled(!isVideoEnabled);
    // Toggle video track
    if (localVideoRef.current?.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !isVideoEnabled;
      }
    }
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    // Toggle audio track
    if (localVideoRef.current?.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const audioTrack = stream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !isAudioEnabled;
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-500';
      case 'waiting': return 'bg-yellow-500';
      case 'in_progress': return 'bg-green-500';
      case 'completed': return 'bg-gray-500';
      case 'cancelled': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Virtual Consultation
              </h1>
              <p className="text-gray-600">
                {consultation.doctor_name} with {consultation.patient_name}
              </p>
              <p className="text-sm text-gray-500">
                {consultation.appointment_date} at {consultation.appointment_time}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge className={`${getStatusColor(consultation.status)} text-white`}>
                {consultation.status.replace('_', ' ').toUpperCase()}
              </Badge>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Video Area */}
          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-0">
                <div className="relative bg-black rounded-lg overflow-hidden" style={{ height: '500px' }}>
                  {/* Jitsi Meet Container */}
                  {consultation.video_provider === 'jitsi' && (
                    <div id="jitsi-container" className="w-full h-full" />
                  )}

                  {/* Fallback Video Elements */}
                  {consultation.video_provider !== 'jitsi' && (
                    <>
                      <video
                        ref={remoteVideoRef}
                        autoPlay
                        playsInline
                        className="w-full h-full object-cover"
                      />
                      <video
                        ref={localVideoRef}
                        autoPlay
                        playsInline
                        muted
                        className="absolute bottom-4 right-4 w-48 h-36 object-cover rounded-lg border-2 border-white"
                      />
                    </>
                  )}

                  {/* Controls Overlay */}
                  <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
                    <div className="flex items-center space-x-4 bg-black bg-opacity-50 rounded-full px-6 py-3">
                      <Button
                        variant={isAudioEnabled ? "default" : "destructive"}
                        size="sm"
                        onClick={toggleAudio}
                        className="rounded-full w-12 h-12"
                      >
                        {isAudioEnabled ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
                      </Button>

                      <Button
                        variant={isVideoEnabled ? "default" : "destructive"}
                        size="sm"
                        onClick={toggleVideo}
                        className="rounded-full w-12 h-12"
                      >
                        {isVideoEnabled ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
                      </Button>

                      {consultation.status === 'scheduled' && user?.role === 'doctor' && (
                        <Button
                          onClick={handleStartConsultation}
                          className="bg-green-600 hover:bg-green-700 rounded-full px-6"
                        >
                          <Phone className="w-5 h-5 mr-2" />
                          Start
                        </Button>
                      )}

                      {consultation.status === 'in_progress' && user?.role === 'doctor' && (
                        <Button
                          onClick={handleEndConsultation}
                          variant="destructive"
                          className="rounded-full px-6"
                        >
                          <PhoneOff className="w-5 h-5 mr-2" />
                          End
                        </Button>
                      )}

                      {consultation.status === 'scheduled' && user?.role === 'patient' && (
                        <Button
                          onClick={handleJoinWaitingRoom}
                          className="bg-blue-600 hover:bg-blue-700 rounded-full px-6"
                        >
                          Join Waiting Room
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsChatOpen(!isChatOpen)}
                        className="rounded-full w-12 h-12"
                      >
                        <MessageCircle className="w-5 h-5" />
                      </Button>

                      <Dialog open={showTechnicalIssueDialog} onOpenChange={setShowTechnicalIssueDialog}>
                        <DialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-full w-12 h-12"
                          >
                            <AlertTriangle className="w-5 h-5" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Report Technical Issue</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium mb-2">Issue Type</label>
                              <select
                                value={technicalIssue.issue_type}
                                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, issue_type: e.target.value }))}
                                className="w-full p-2 border rounded-md"
                              >
                                <option value="">Select issue type</option>
                                <option value="audio">Audio Problem</option>
                                <option value="video">Video Problem</option>
                                <option value="connection">Connection Issue</option>
                                <option value="screen_share">Screen Share Problem</option>
                                <option value="other">Other</option>
                              </select>
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-2">Description</label>
                              <Textarea
                                value={technicalIssue.description}
                                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, description: e.target.value }))}
                                placeholder="Describe the issue..."
                                rows={3}
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-2">Severity</label>
                              <select
                                value={technicalIssue.severity}
                                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, severity: e.target.value }))}
                                className="w-full p-2 border rounded-md"
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                              </select>
                            </div>
                            <Button onClick={handleReportIssue} className="w-full">
                              Report Issue
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>

                  {/* Connection Quality Indicator */}
                  <div className="absolute top-4 right-4">
                    <div className="flex items-center space-x-2 bg-black bg-opacity-50 rounded-full px-3 py-2">
                      <div className={`w-3 h-3 rounded-full ${
                        connectionQuality === 'excellent' ? 'bg-green-500' :
                        connectionQuality === 'good' ? 'bg-yellow-500' :
                        connectionQuality === 'fair' ? 'bg-orange-500' : 'bg-red-500'
                      }`} />
                      <span className="text-white text-sm capitalize">{connectionQuality}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Participants */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Participants ({participants.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {participants.map((participant, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                      <span className="text-sm">{participant}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Chat */}
            {isChatOpen && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center">
                      <MessageCircle className="w-5 h-5 mr-2" />
                      Chat
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsChatOpen(false)}
                    >
                      ×
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Messages */}
                    <div className="h-64 overflow-y-auto space-y-2 border rounded-md p-2">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`p-2 rounded-md ${
                            message.sender_name === user?.first_name + ' ' + user?.last_name
                              ? 'bg-blue-100 ml-4'
                              : 'bg-gray-100 mr-4'
                          }`}
                        >
                          <div className="text-xs text-gray-500 mb-1">
                            {message.sender_name} • {new Date(message.timestamp).toLocaleTimeString()}
                            {message.is_private && <span className="ml-1 text-red-500">(Private)</span>}
                          </div>
                          <div className="text-sm">{message.message}</div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input */}
                    <form onSubmit={handleSendMessage} className="flex space-x-2">
                      <Input
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1"
                      />
                      <Button type="submit" size="sm">
                        Send
                      </Button>
                    </form>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsultationRoom;