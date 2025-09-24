import { apiService } from './api';

export interface MetricsOverview {
  period: {
    from: string;
    to: string;
  };
  funnel: {
    leads_new: number;
    leads_contacted: number;
    leads_qualified: number;
    leads_booked: number;
    leads_showed: number;
    contact_rate: number;
    qualification_rate: number;
    booking_rate: number;
    show_rate: number;
  };
  realtime: any;
}

export interface TelephonyMetrics {
  period: {
    from: string;
    to: string;
  };
  totals: {
    calls_initiated: number;
    calls_answered: number;
    calls_completed: number;
    answer_rate: number;
    completion_rate: number;
    total_talk_time_minutes: number;
    total_cost_dollars: number;
    avg_cost_per_call: number;
  };
  daily_breakdown: Array<{
    date: string;
    calls_initiated: number;
    calls_answered: number;
    answer_rate: number;
    avg_talk_time_minutes: number;
  }>;
}

export interface WhatsAppMetrics {
  period: {
    from: string;
    to: string;
  };
  totals: {
    messages_sent: number;
    messages_delivered: number;
    messages_read: number;
    messages_received: number;
    delivery_rate: number;
    read_rate: number;
    response_rate: number;
  };
}

export interface NoShowMetrics {
  total_appointments: number;
  no_shows: number;
  no_show_rate: number;
  reasons: Array<{
    reason: string;
    count: number;
  }>;
}

export const metricsService = {
  async getOverview(): Promise<MetricsOverview | null> {
    const response = await apiService.get<MetricsOverview>('/metrics/overview');
    return response.data || null;
  },

  async getTelephonyMetrics(): Promise<TelephonyMetrics | null> {
    const response = await apiService.get<TelephonyMetrics>('/metrics/telephony');
    return response.data || null;
  },

  async getWhatsAppMetrics(): Promise<WhatsAppMetrics | null> {
    const response = await apiService.get<WhatsAppMetrics>('/metrics/whatsapp');
    return response.data || null;
  },

  async getNoShowMetrics(): Promise<NoShowMetrics | null> {
    const response = await apiService.get<NoShowMetrics>('/metrics/no_shows');
    return response.data || null;
  },

  async exportMetrics(): Promise<Blob | null> {
    try {
      const response = await fetch('/api/v1/export/metrics.csv');
      if (response.ok) {
        return await response.blob();
      }
      return null;
    } catch (error) {
      console.error('Failed to export metrics:', error);
      return null;
    }
  },
};