import { apiService } from './api';

export interface Call {
  id: string;
  vapi_call_id?: string;
  twilio_call_sid?: string;
  lead_id: string;
  lead_name?: string;
  lead_phone?: string;
  direction: 'inbound' | 'outbound';
  status: 'queued' | 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer' | 'cancelled';
  outcome?: 'successful' | 'no_answer' | 'busy' | 'voicemail' | 'wrong_number' | 'interested' | 'not_interested' | 'callback_requested' | 'appointment_booked' | 'technical_issue';
  from_number: string;
  to_number: string;
  duration_seconds: number;
  talk_time_seconds: number;
  recording_url?: string;
  transcript?: string;
  transcript_summary?: string;
  ai_sentiment?: string;
  ai_intent?: string;
  cost_cents: number;
  error_code?: string;
  error_message?: string;
  queued_at: string;
  initiated_at?: string;
  answered_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CallStats {
  total_calls: number;
  answered_calls: number;
  completed_calls: number;
  no_answer_calls: number;
  busy_calls: number;
  failed_calls: number;
  escalated_calls: number;
  average_duration: number;
  total_cost_dollars: number;
  answer_rate: number;
  completion_rate: number;
}

export interface CallRecording {
  recording_url: string;
}

export interface CallTranscript {
  call_id: string;
  transcript?: string;
  summary?: string;
  ai_sentiment?: string;
  ai_intent?: string;
  vapi_function_calls: Array<{
    function_name: string;
    parameters: any;
    result?: any;
    timestamp: string;
  }>;
}

export const callsService = {
  async getCalls(filters?: {
    status?: string;
    direction?: string;
    lead_id?: string;
    date_from?: string;
    date_to?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<Call[] | null> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const response = await apiService.get<Call[]>(`/calls?${params.toString()}`);
    return response.data || null;
  },

  async getCall(id: string): Promise<Call | null> {
    const response = await apiService.get<Call>(`/calls/${id}`);
    return response.data || null;
  },

  async getCallStats(filters?: {
    date_from?: string;
    date_to?: string;
  }): Promise<CallStats | null> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const response = await apiService.get<CallStats>(`/calls/stats?${params.toString()}`);
    return response.data || null;
  },

  async getCallRecording(callId: string): Promise<CallRecording | null> {
    const response = await apiService.get<CallRecording>(`/calls/${callId}/recording`);
    return response.data || null;
  },

  async getCallTranscript(callId: string): Promise<CallTranscript | null> {
    const response = await apiService.get<CallTranscript>(`/calls/${callId}/transcript`);
    return response.data || null;
  },

  async playRecording(recordingUrl: string): Promise<void> {
    // Open recording in new tab or use audio player
    window.open(recordingUrl, '_blank');
  },

  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  },

  formatCost(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  },

  getStatusColor(status: string): string {
    switch (status) {
      case 'completed':
        return 'bg-success-soft text-success';
      case 'no_answer':
        return 'bg-warning-soft text-warning';
      case 'busy':
        return 'bg-muted text-muted-foreground';
      case 'failed':
        return 'bg-destructive-soft text-destructive';
      case 'answered':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-muted text-muted-foreground';
    }
  },

  getOutcomeColor(outcome: string): string {
    switch (outcome) {
      case 'appointment_booked':
      case 'interested':
        return 'text-success';
      case 'not_interested':
        return 'text-destructive';
      case 'callback_requested':
        return 'text-warning';
      case 'technical_issue':
        return 'text-destructive';
      default:
        return 'text-muted-foreground';
    }
  },
};