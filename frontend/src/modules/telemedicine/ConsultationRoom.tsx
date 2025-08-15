import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Video, VideoOff, Mic, MicOff, Monitor, MonitorOff,
  MessageCircle, Users, Settings, AlertTriangle, Phone,
  MoreVertical, Camera, Volume2, VolumeX, PhoneOff,
  Circle, StopCircle, FileText, Clock, Maximize2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
  DialogDescription, DialogFooter 
} from '../../components/ui/dialog';
import { useConsultations, type Consultation } from '../../hooks/useConsultations';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';

interface ConsultationRoomProps {
  consultation?: Consultation;
}

export const ConsultationRoom: React.FC<ConsultationRoomProps> = ({ consultation: propConsultation }) => {
  const { consultationId } = useParams<{ consultationId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const {
    currentConsultation,
    fetchConsultationById,
    startConsultation,
    endConsultation,
    joinConsultation,
    leaveConsultation,
    messages,
    participants,
    technicalIssues,
    reportTechnicalIssue,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
    loading
  } = useConsultations();

  // Local state for UI controls
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isParticipantsOpen, setIsParticipantsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [currentMessage, setCurrentMessage] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Technical issue state
  const [isReportingIssue, setIsReportingIssue] = useState(false);
  const [technicalIssue, setTechnicalIssue] = useState({
    issue_type: 'audio',
    severity: 'medium',
    description: ''
  });

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Get the consultation to work with
  const consultation = propConsultation || currentConsultation;

  // Initialize consultation
  useEffect(() => {
    if (consultationId && !consultation) {
      fetchConsultationById(consultationId);
    }
  }, [consultationId, consultation, fetchConsultationById]);

  // Connect WebSocket when consultation is available
  useEffect(() => {
    if (consultation?.id) {
      connectWebSocket(consultation.id);
      return () => disconnectWebSocket();
    }
  }, [consultation?.id, connectWebSocket, disconnectWebSocket]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle video platform integration
  const openVideoMeeting = useCallback(() => {
    if (!consultation?.meeting_url) {
      toast.error('Meeting URL not available');
      return;
    }

    switch (consultation.video_provider) {
      case 'zoom':
        toast('Redirecting to Zoom meeting...');
        window.open(consultation.meeting_url, '_blank');
        break;
      case 'google_meet':
        toast('Redirecting to Google Meet...');
        window.open(consultation.meeting_url, '_blank');
        break;
      case 'jitsi':
        // For Jitsi, we can embed it directly or open in new window
        window.open(consultation.meeting_url, '_blank');
        break;
      default:
        toast.error('Unsupported video provider');
    }
  }, [consultation]);

  // Consultation control functions
  const handleStartConsultation = async () => {
    if (!consultation?.id) return;
    
    try {
      await startConsultation(consultation.id);
      await joinConsultation(consultation.id);
      openVideoMeeting();
    } catch (error) {
      console.error('Failed to start consultation:', error);
    }
  };

  const handleEndConsultation = async () => {
    if (!consultation?.id) return;
    
    try {
      await endConsultation(consultation.id);
      toast.success('Consultation ended successfully');
      navigate('/consultations');
    } catch (error) {
      console.error('Failed to end consultation:', error);
    }
  };

  const handleJoinConsultation = async () => {
    if (!consultation?.id) return;
    
    try {
      await joinConsultation(consultation.id);
      openVideoMeeting();
    } catch (error) {
      console.error('Failed to join consultation:', error);
    }
  };

  const handleLeaveConsultation = async () => {
    if (!consultation?.id) return;
    
    try {
      await leaveConsultation(consultation.id);
      navigate('/consultations');
    } catch (error) {
      console.error('Failed to leave consultation:', error);
    }
  };

  // Chat functions
  const sendMessage = useCallback(async () => {
    if (!currentMessage.trim() || !consultation?.id) return;

    try {
      sendWebSocketMessage({
        type: 'chat_message',
        consultation_id: consultation.id,
        message: currentMessage,
        message_type: 'text'
      });
      setCurrentMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    }
  }, [currentMessage, consultation?.id, sendWebSocketMessage]);

  // Technical issue reporting
  const handleReportTechnicalIssue = async () => {
    if (!consultation?.id) return;

    try {
      await reportTechnicalIssue({
        consultation: consultation.id,
        issue_type: technicalIssue.issue_type,
        severity: technicalIssue.severity,
        description: technicalIssue.description
      });
      
      setIsReportingIssue(false);
      setTechnicalIssue({ issue_type: 'audio', severity: 'medium', description: '' });
      toast.success('Technical issue reported');
    } catch (error) {
      console.error('Failed to report technical issue:', error);
    }
  };

  // Media controls (simulated - would integrate with actual WebRTC)
  const toggleVideo = () => {
    setIsVideoEnabled(!isVideoEnabled);
    toast(isVideoEnabled ? 'Video disabled' : 'Video enabled');
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    toast(isAudioEnabled ? 'Audio muted' : 'Audio unmuted');
  };

  const toggleScreenShare = () => {
    setIsScreenSharing(!isScreenSharing);
    toast(isScreenSharing ? 'Screen sharing stopped' : 'Screen sharing started');
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    toast(isRecording ? 'Recording stopped' : 'Recording started');
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-lg">Loading consultation...</p>
        </div>
      </div>
    );
  }

  if (!consultation) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Consultation Not Found</h1>
          <p className="mt-2 text-gray-600">The consultation you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/consultations')} className="mt-4">
            Back to Consultations
          </Button>
        </div>
      </div>
    );
  }

  const canStartConsultation = consultation.can_start && user?.role === 'doctor';
  const canJoinConsultation = consultation.status === 'in_progress' || consultation.status === 'waiting';
  const isInConsultation = consultation.status === 'in_progress';

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">
              Consultation with {user?.role === 'doctor' ? consultation.patient_name : consultation.doctor_name}
            </h1>
            <Badge 
              className={`${
                consultation.status === 'in_progress' ? 'bg-green-500' : 
                consultation.status === 'waiting' ? 'bg-yellow-500' : 
                'bg-gray-500'
              }`}
            >
              {consultation.status.replace('_', ' ').toUpperCase()}
            </Badge>
            <Badge variant="outline" className="text-white border-white">
              {consultation.video_provider.toUpperCase()}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Connection Quality */}
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                connectionQuality === 'excellent' ? 'bg-green-500' :
                connectionQuality === 'good' ? 'bg-yellow-500' :
                connectionQuality === 'fair' ? 'bg-orange-500' : 'bg-red-500'
              }`} />
              <span className="text-sm capitalize">{connectionQuality}</span>
            </div>

            {/* WebSocket Status */}
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>

            <Button variant="ghost" size="sm" onClick={() => navigate('/consultations')}>
              Exit
            </Button>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Main Video Area */}
        <div className="flex-1 flex flex-col">
          {/* Video Container */}
          <div className="flex-1 relative bg-black">
            {/* Remote Video */}
            <video
              ref={remoteVideoRef}
              className="w-full h-full object-cover"
              autoPlay
              playsInline
            />
            
            {/* Local Video (Picture-in-Picture) */}
            <div className="absolute top-4 right-4 w-48 h-36 bg-gray-800 rounded-lg overflow-hidden border-2 border-white">
              <video
                ref={videoRef}
                className="w-full h-full object-cover"
                autoPlay
                playsInline
                muted
              />
              {!isVideoEnabled && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                  <VideoOff className="w-8 h-8 text-gray-400" />
                </div>
              )}
            </div>

                         {/* Recording Indicator */}
             {isRecording && (
               <div className="absolute top-4 left-4 flex items-center space-x-2 bg-red-600 px-3 py-1 rounded-full">
                 <Circle className="w-4 h-4 fill-current" />
                 <span className="text-sm font-medium">Recording</span>
               </div>
             )}

            {/* Screen Share Indicator */}
            {isScreenSharing && (
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 px-3 py-1 rounded-full">
                <span className="text-sm font-medium">Screen Sharing</span>
              </div>
            )}

            {/* Consultation not started overlay */}
            {!isInConsultation && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold mb-4">Consultation Ready</h2>
                  <p className="text-gray-300 mb-6">
                    {canStartConsultation 
                      ? 'Start the consultation when ready'
                      : canJoinConsultation 
                        ? 'Join the consultation'
                        : 'Waiting for consultation to begin'
                    }
                  </p>
                  
                  {canStartConsultation && (
                    <Button onClick={handleStartConsultation} size="lg" className="mr-4">
                      Start Consultation
                    </Button>
                  )}
                  
                  {canJoinConsultation && !canStartConsultation && (
                    <Button onClick={handleJoinConsultation} size="lg" className="mr-4">
                      Join Meeting
                    </Button>
                  )}
                  
                  <Button onClick={openVideoMeeting} variant="outline" size="lg">
                    Open {consultation.video_provider.replace('_', ' ')} Meeting
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="bg-gray-800 p-4">
            <div className="flex items-center justify-center space-x-4">
              {/* Audio Control */}
              <Button
                variant={isAudioEnabled ? "default" : "destructive"}
                size="lg"
                onClick={toggleAudio}
                className="rounded-full w-12 h-12"
              >
                {isAudioEnabled ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
              </Button>

              {/* Video Control */}
              <Button
                variant={isVideoEnabled ? "default" : "destructive"}
                size="lg"
                onClick={toggleVideo}
                className="rounded-full w-12 h-12"
              >
                {isVideoEnabled ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
              </Button>

              {/* Screen Share */}
              <Button
                variant={isScreenSharing ? "secondary" : "outline"}
                size="lg"
                onClick={toggleScreenShare}
                className="rounded-full w-12 h-12"
              >
                {isScreenSharing ? <MonitorOff className="w-5 h-5" /> : <Monitor className="w-5 h-5" />}
              </Button>

              {/* Recording */}
              <Button
                variant={isRecording ? "destructive" : "outline"}
                size="lg"
                onClick={toggleRecording}
                className="rounded-full w-12 h-12"
              >
                                 {isRecording ? <StopCircle className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
              </Button>

              {/* End Call */}
              {isInConsultation && (
                <Button
                  variant="destructive"
                  size="lg"
                  onClick={handleEndConsultation}
                  className="rounded-full w-12 h-12"
                >
                  <PhoneOff className="w-5 h-5" />
                </Button>
              )}

              {/* Fullscreen */}
              <Button
                variant="outline"
                size="lg"
                onClick={toggleFullscreen}
                className="rounded-full w-12 h-12"
              >
                <Maximize2 className="w-5 h-5" />
              </Button>

              {/* More Options */}
              <Button
                variant="outline"
                size="lg"
                onClick={() => setIsSettingsOpen(true)}
                className="rounded-full w-12 h-12"
              >
                <MoreVertical className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
          {/* Sidebar Tabs */}
          <div className="flex border-b border-gray-700">
            <button
              onClick={() => setIsChatOpen(true)}
              className={`flex-1 p-3 text-sm font-medium ${
                isChatOpen ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <MessageCircle className="w-4 h-4 mx-auto mb-1" />
              Chat ({messages.length})
            </button>
            <button
              onClick={() => setIsParticipantsOpen(true)}
              className={`flex-1 p-3 text-sm font-medium ${
                isParticipantsOpen ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Users className="w-4 h-4 mx-auto mb-1" />
              People ({participants.length})
            </button>
          </div>

          {/* Chat Panel */}
          {isChatOpen && (
            <div className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((message, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-blue-400">
                        {message.sender_name}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-200">{message.message}</p>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
              
              <div className="p-4 border-t border-gray-700">
                <div className="flex space-x-2">
                  <Textarea
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 bg-gray-700 border-gray-600 text-white"
                    rows={2}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                  />
                  <Button onClick={sendMessage} disabled={!currentMessage.trim()}>
                    Send
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Participants Panel */}
          {isParticipantsOpen && (
            <div className="flex-1 overflow-y-auto p-4">
              <h3 className="text-lg font-semibold mb-4">Participants</h3>
              <div className="space-y-3">
                {participants.map((participant) => (
                  <div key={participant.id} className="flex items-center justify-between bg-gray-700 rounded-lg p-3">
                    <div>
                      <p className="font-medium">{participant.user_name}</p>
                      <p className="text-sm text-gray-400 capitalize">{participant.role}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {participant.joined_at && (
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Technical Issue Report Dialog */}
      <Dialog open={isReportingIssue} onOpenChange={setIsReportingIssue}>
        <DialogContent className="bg-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>Report Technical Issue</DialogTitle>
            <DialogDescription>
              Help us improve your experience by reporting any technical issues.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Issue Type</label>
              <select
                value={technicalIssue.issue_type}
                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, issue_type: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-md p-2"
              >
                <option value="audio">Audio Problem</option>
                <option value="video">Video Problem</option>
                <option value="connection">Connection Issue</option>
                <option value="screen_share">Screen Share Problem</option>
                <option value="recording">Recording Issue</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Severity</label>
              <select
                value={technicalIssue.severity}
                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, severity: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-md p-2"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <Textarea
                value={technicalIssue.description}
                onChange={(e) => setTechnicalIssue(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Please describe the issue in detail..."
                className="bg-gray-700 border-gray-600 text-white"
                rows={4}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsReportingIssue(false)}>
              Cancel
            </Button>
            <Button onClick={handleReportTechnicalIssue}>
              Report Issue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Quick Actions Floating Button */}
      <div className="fixed bottom-4 left-4">
        <Dialog>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              size="lg"
              className="rounded-full w-14 h-14 shadow-lg"
            >
              <AlertTriangle className="w-6 h-6" />
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-800 text-white">
            <DialogHeader>
              <DialogTitle>Quick Actions</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <Button
                onClick={() => {
                  setIsReportingIssue(true);
                }}
                variant="outline"
                className="h-16 flex flex-col items-center justify-center space-y-1"
              >
                <AlertTriangle className="w-5 h-5" />
                <span className="text-xs">Report Issue</span>
              </Button>
              <Button
                onClick={openVideoMeeting}
                variant="outline"
                className="h-16 flex flex-col items-center justify-center space-y-1"
              >
                <Video className="w-5 h-5" />
                <span className="text-xs">Open Meeting</span>
              </Button>
              <Button
                onClick={() => setIsChatOpen(true)}
                variant="outline"
                className="h-16 flex flex-col items-center justify-center space-y-1"
              >
                <MessageCircle className="w-5 h-5" />
                <span className="text-xs">Open Chat</span>
              </Button>
              <Button
                onClick={handleLeaveConsultation}
                variant="destructive"
                className="h-16 flex flex-col items-center justify-center space-y-1"
              >
                <PhoneOff className="w-5 h-5" />
                <span className="text-xs">Leave</span>
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};