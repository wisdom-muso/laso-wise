import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

export enum VideoProvider {
  JITSI = 'jitsi',
  ZOOM = 'zoom',
  GOOGLE_MEET = 'google_meet',
}

@Entity('video_provider_configs')
@Index(['provider'], { unique: true })
export class VideoProviderConfig {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({
    type: 'enum',
    enum: VideoProvider,
    unique: true,
  })
  provider: VideoProvider;

  @Column({ name: 'is_active', default: true })
  isActive: boolean;

  @Column({ name: 'api_key', nullable: true })
  apiKey: string | null;

  @Column({ name: 'api_secret', nullable: true })
  apiSecret: string | null;

  @Column({ name: 'webhook_url', nullable: true })
  webhookUrl: string;

  @Column({ name: 'max_participants', default: 2 })
  maxParticipants: number;

  @Column({ name: 'recording_enabled', default: true })
  recordingEnabled: boolean;

  @Column({ name: 'auto_recording', default: false })
  autoRecording: boolean;

  @Column({ name: 'waiting_room_enabled', default: true })
  waitingRoomEnabled: boolean;

  @Column({ name: 'authentication_required', default: false })
  authenticationRequired: boolean;

  @Column({ name: 'meeting_timeout_minutes', default: 120 })
  meetingTimeoutMinutes: number;

  @Column({ name: 'settings_json', type: 'jsonb', default: {} })
  settingsJson: Record<string, any>;

  @Column({ name: 'rate_limit_per_minute', default: 60 })
  rateLimitPerMinute: number;

  @Column({ name: 'priority_order', default: 1 })
  priorityOrder: number;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Helper methods
  getProviderDisplayName(): string {
    const displayNames = {
      [VideoProvider.JITSI]: 'Jitsi Meet',
      [VideoProvider.ZOOM]: 'Zoom',
      [VideoProvider.GOOGLE_MEET]: 'Google Meet',
    };
    return displayNames[this.provider] || 'Unknown';
  }

  isConfigured(): boolean {
    switch (this.provider) {
      case VideoProvider.JITSI:
        return true; // Jitsi can work without API keys
      case VideoProvider.ZOOM:
        return !!(this.apiKey && this.apiSecret);
      case VideoProvider.GOOGLE_MEET:
        return !!(this.apiKey && this.apiSecret);
      default:
        return false;
    }
  }

  canCreateMeeting(): boolean {
    return this.isActive && this.isConfigured();
  }

  hasRecordingCapability(): boolean {
    return this.recordingEnabled && this.canCreateMeeting();
  }

  hasWaitingRoomCapability(): boolean {
    return this.waitingRoomEnabled && this.canCreateMeeting();
  }

  getMaxDuration(): number {
    return this.meetingTimeoutMinutes;
  }

  updateSettings(newSettings: Record<string, any>): void {
    this.settingsJson = { ...this.settingsJson, ...newSettings };
  }

  getSettings(): Record<string, any> {
    return this.settingsJson || {};
  }

  getSetting(key: string, defaultValue?: any): any {
    return this.settingsJson?.[key] ?? defaultValue;
  }

  setSetting(key: string, value: any): void {
    if (!this.settingsJson) {
      this.settingsJson = {};
    }
    this.settingsJson[key] = value;
  }

  enable(): void {
    this.isActive = true;
  }

  disable(): void {
    this.isActive = false;
  }

  updateApiCredentials(apiKey: string, apiSecret?: string): void {
    this.apiKey = apiKey;
    if (apiSecret) {
      this.apiSecret = apiSecret;
    }
  }

  clearApiCredentials(): void {
    this.apiKey = null;
    this.apiSecret = null;
  }

  updateWebhookUrl(url: string): void {
    this.webhookUrl = url;
  }

  updateRateLimit(limitPerMinute: number): void {
    this.rateLimitPerMinute = Math.max(1, limitPerMinute);
  }

  updatePriority(priority: number): void {
    this.priorityOrder = Math.max(1, priority);
  }

  enableRecording(): void {
    this.recordingEnabled = true;
  }

  disableRecording(): void {
    this.recordingEnabled = false;
    this.autoRecording = false;
  }

  enableAutoRecording(): void {
    this.recordingEnabled = true;
    this.autoRecording = true;
  }

  disableAutoRecording(): void {
    this.autoRecording = false;
  }

  enableWaitingRoom(): void {
    this.waitingRoomEnabled = true;
  }

  disableWaitingRoom(): void {
    this.waitingRoomEnabled = false;
  }

  requireAuthentication(): void {
    this.authenticationRequired = true;
  }

  removeAuthenticationRequirement(): void {
    this.authenticationRequired = false;
  }

  updateMaxParticipants(max: number): void {
    this.maxParticipants = Math.max(2, max);
  }

  updateMeetingTimeout(minutes: number): void {
    this.meetingTimeoutMinutes = Math.max(15, minutes);
  }
}