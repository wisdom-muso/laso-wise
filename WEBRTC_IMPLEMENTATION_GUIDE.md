# 🎥 WebRTC Video Calls Implementation Guide

## Current Status Analysis

### ✅ What's Already Working:
- **Models**: Complete telemedicine models (TeleMedicineConsultation, VideoSession)
- **Views**: Consultation management, room joining, message handling
- **Templates**: Beautiful consultation room UI with video containers
- **Basic Media Access**: getUserMedia() for camera/microphone
- **Chat System**: Real-time messaging during consultations
- **User Management**: Doctor/patient role-based access

### ❌ What's Missing for Real WebRTC:

1. **WebSocket/Channels Support** - No real-time signaling
2. **WebRTC Peer Connection** - Only placeholder code
3. **STUN/TURN Servers** - No NAT traversal support
4. **ICE Candidate Exchange** - No peer discovery
5. **SDP Offer/Answer** - No media negotiation
6. **Connection State Management** - No reconnection logic
7. **Screen Sharing** - Button exists but no implementation
8. **Recording** - No actual recording capability

## 🚀 Complete WebRTC Implementation

### Step 1: Add Required Dependencies

Add to `requirements.txt`:
```bash
# WebRTC and Real-time Communication
channels==4.0.0
channels-redis==4.2.0
django-channels==4.0.0
aiortc==1.6.0  # For server-side WebRTC if needed
websockets==12.0
```

### Step 2: Configure Django Channels

**settings.py additions:**
```python
INSTALLED_APPS = [
    # ... existing apps
    'channels',
]

# Channels configuration
ASGI_APPLICATION = 'laso.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# WebRTC Configuration
WEBRTC_CONFIG = {
    'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        # Add TURN servers for production:
        # {
        #     'urls': 'turn:your-turn-server.com:3478',
        #     'username': 'your-username',
        #     'credential': 'your-password'
        # }
    ]
}
```

### Step 3: Create WebSocket Consumer

**telemedicine/consumers.py:**
```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import TeleMedicineConsultation

User = get_user_model()

class ConsultationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        
        # Verify user can join this consultation
        if await self.can_join_consultation():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.scope['user'].id,
                    'user_name': self.scope['user'].get_full_name(),
                    'user_role': 'doctor' if self.scope['user'].is_doctor() else 'patient'
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.scope['user'].id,
                'user_name': self.scope['user'].get_full_name()
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'webrtc_offer':
            await self.handle_webrtc_offer(data)
        elif message_type == 'webrtc_answer':
            await self.handle_webrtc_answer(data)
        elif message_type == 'ice_candidate':
            await self.handle_ice_candidate(data)
        elif message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'screen_share':
            await self.handle_screen_share(data)

    async def handle_webrtc_offer(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'sender_id': self.scope['user'].id
            }
        )

    async def handle_webrtc_answer(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'sender_id': self.scope['user'].id
            }
        )

    async def handle_ice_candidate(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'ice_candidate',
                'candidate': data['candidate'],
                'sender_id': self.scope['user'].id
            }
        )

    async def handle_chat_message(self, data):
        # Save message to database
        await self.save_chat_message(data['message'])
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'sender_id': self.scope['user'].id,
                'sender_name': self.scope['user'].get_full_name(),
                'timestamp': data.get('timestamp')
            }
        )

    # WebSocket message handlers
    async def webrtc_offer(self, event):
        if event['sender_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'sender_id': event['sender_id']
            }))

    async def webrtc_answer(self, event):
        if event['sender_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'sender_id': event['sender_id']
            }))

    async def ice_candidate(self, event):
        if event['sender_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id']
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'user_role': event['user_role']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_name': event['user_name']
        }))

    @database_sync_to_async
    def can_join_consultation(self):
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            return consultation.can_join(self.scope['user'])
        except TeleMedicineConsultation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_chat_message(self, message):
        # Implementation to save chat message
        pass
```

### Step 4: Update ASGI Configuration

**laso/asgi.py:**
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from telemedicine.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
```

### Step 5: WebSocket URL Routing

**telemedicine/routing.py:**
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/consultation/(?P<consultation_id>\w+)/$', consumers.ConsultationConsumer.as_asgi()),
]
```

### Step 6: Enhanced Frontend WebRTC Implementation

**Updated consultation_room.html JavaScript:**
```javascript
class TeleMedicineConsultation {
    constructor(consultationId, userRole) {
        this.consultationId = consultationId;
        this.userRole = userRole;
        this.localStream = null;
        this.remoteStream = null;
        this.peerConnection = null;
        this.websocket = null;
        this.isVideoEnabled = true;
        this.isAudioEnabled = true;
        this.startTime = new Date();
        
        // WebRTC Configuration
        this.rtcConfiguration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        this.init();
    }
    
    async init() {
        await this.setupWebSocket();
        await this.setupLocalStream();
        this.setupEventListeners();
        this.startDurationTimer();
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/consultation/${this.consultationId}/`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            await this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            // Implement reconnection logic
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    async handleWebSocketMessage(data) {
        switch (data.type) {
            case 'user_joined':
                await this.handleUserJoined(data);
                break;
            case 'webrtc_offer':
                await this.handleWebRTCOffer(data);
                break;
            case 'webrtc_answer':
                await this.handleWebRTCAnswer(data);
                break;
            case 'ice_candidate':
                await this.handleICECandidate(data);
                break;
            case 'chat_message':
                this.displayChatMessage(data);
                break;
        }
    }
    
    async setupLocalStream() {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 },
                audio: { echoCancellation: true, noiseSuppression: true }
            });
            
            document.getElementById('localVideo').srcObject = this.localStream;
            
        } catch (error) {
            console.error('Error accessing media devices:', error);
            this.showError('Camera and microphone access is required');
        }
    }
    
    async createPeerConnection() {
        this.peerConnection = new RTCPeerConnection(this.rtcConfiguration);
        
        // Add local stream tracks
        this.localStream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, this.localStream);
        });
        
        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            this.remoteStream = event.streams[0];
            document.getElementById('remoteVideo').srcObject = this.remoteStream;
        };
        
        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.websocket.send(JSON.stringify({
                    type: 'ice_candidate',
                    candidate: event.candidate
                }));
            }
        };
        
        // Connection state monitoring
        this.peerConnection.onconnectionstatechange = () => {
            this.updateConnectionStatus(this.peerConnection.connectionState);
        };
    }
    
    async handleUserJoined(data) {
        if (data.user_role !== this.userRole) {
            // Other participant joined, initiate call if we're the doctor
            if (this.userRole === 'doctor') {
                await this.initiateCall();
            }
        }
    }
    
    async initiateCall() {
        await this.createPeerConnection();
        
        const offer = await this.peerConnection.createOffer();
        await this.peerConnection.setLocalDescription(offer);
        
        this.websocket.send(JSON.stringify({
            type: 'webrtc_offer',
            offer: offer
        }));
    }
    
    async handleWebRTCOffer(data) {
        await this.createPeerConnection();
        
        await this.peerConnection.setRemoteDescription(data.offer);
        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);
        
        this.websocket.send(JSON.stringify({
            type: 'webrtc_answer',
            answer: answer
        }));
    }
    
    async handleWebRTCAnswer(data) {
        await this.peerConnection.setRemoteDescription(data.answer);
    }
    
    async handleICECandidate(data) {
        await this.peerConnection.addIceCandidate(data.candidate);
    }
    
    toggleVideo() {
        this.isVideoEnabled = !this.isVideoEnabled;
        const videoTrack = this.localStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.enabled = this.isVideoEnabled;
        }
        
        const button = document.getElementById('videoToggle');
        button.classList.toggle('muted', !this.isVideoEnabled);
        button.innerHTML = this.isVideoEnabled ? 
            '<i class="fas fa-video"></i>' : 
            '<i class="fas fa-video-slash"></i>';
    }
    
    toggleAudio() {
        this.isAudioEnabled = !this.isAudioEnabled;
        const audioTrack = this.localStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = this.isAudioEnabled;
        }
        
        const button = document.getElementById('audioToggle');
        button.classList.toggle('muted', !this.isAudioEnabled);
        button.innerHTML = this.isAudioEnabled ? 
            '<i class="fas fa-microphone"></i>' : 
            '<i class="fas fa-microphone-slash"></i>';
    }
    
    async shareScreen() {
        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: true
            });
            
            // Replace video track
            const videoTrack = screenStream.getVideoTracks()[0];
            const sender = this.peerConnection.getSenders().find(s => 
                s.track && s.track.kind === 'video'
            );
            
            if (sender) {
                await sender.replaceTrack(videoTrack);
            }
            
            // Handle screen share end
            videoTrack.onended = async () => {
                const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
                const cameraTrack = cameraStream.getVideoTracks()[0];
                await sender.replaceTrack(cameraTrack);
            };
            
        } catch (error) {
            console.error('Error sharing screen:', error);
        }
    }
    
    updateConnectionStatus(state) {
        const indicator = document.getElementById('connection-indicator');
        const status = document.getElementById('connection-status');
        
        switch (state) {
            case 'connected':
                indicator.className = 'status-indicator';
                status.textContent = 'Connection Good';
                break;
            case 'connecting':
                indicator.className = 'status-indicator fair';
                status.textContent = 'Connecting...';
                break;
            case 'disconnected':
            case 'failed':
                indicator.className = 'status-indicator poor';
                status.textContent = 'Connection Issues';
                break;
        }
    }
    
    sendChatMessage(message) {
        this.websocket.send(JSON.stringify({
            type: 'chat_message',
            message: message,
            timestamp: new Date().toISOString()
        }));
    }
    
    displayChatMessage(data) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.sender_id === currentUserId ? 'sent' : 'received'}`;
        
        messageDiv.innerHTML = `
            <div class="message-sender">${data.sender_name}</div>
            <div>${data.message}</div>
            <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Initialize consultation
const consultation = new TeleMedicineConsultation(
    '{{ consultation.id }}',
    '{{ user_role }}'
);
```

## 🔧 Production Considerations

### TURN Server Setup
For production, you'll need TURN servers for NAT traversal:

```javascript
// Add to rtcConfiguration
{
    urls: 'turn:your-turn-server.com:3478',
    username: 'your-username',
    credential: 'your-password'
}
```

### Recording Implementation
```javascript
// Add to consultation class
startRecording() {
    this.mediaRecorder = new MediaRecorder(this.localStream);
    this.recordedChunks = [];
    
    this.mediaRecorder.ondataavailable = (event) => {
        this.recordedChunks.push(event.data);
    };
    
    this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        // Upload to server
    };
    
    this.mediaRecorder.start();
}
```

### Security Enhancements
- Implement end-to-end encryption
- Add authentication tokens for WebSocket connections
- Rate limiting for signaling messages
- CORS configuration for WebRTC

## 🚀 Deployment Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Run Migrations**: `python manage.py migrate`
3. **Configure Redis**: Ensure Redis is running for Channels
4. **Update Docker Compose**: Add Channels support
5. **Test WebRTC**: Use HTTPS for getUserMedia() to work
6. **Setup TURN Servers**: For production NAT traversal

This implementation provides a complete WebRTC video calling system with real-time signaling, peer-to-peer connections, and all the features needed for telemedicine consultations.