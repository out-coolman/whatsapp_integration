import { apiService } from './api';

export interface Lead {
  id: string;
  helena_id?: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  email?: string;
  phone?: string;
  stage: 'new' | 'contacted' | 'qualified' | 'proposed' | 'booked' | 'confirmed';
  classification: 'hot' | 'warm' | 'cold';
  source: string;
  tags: string[];
  notes?: string;
  assigned_agent_id?: string;
  created_at: string;
  updated_at: string;
  last_contacted_at?: string;
}

export interface CreateLeadRequest {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  notes?: string;
  assigned_agent_id?: string;
  tags?: string[];
  source?: string;
}

export interface UpdateLeadRequest {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  stage?: Lead['stage'];
  classification?: Lead['classification'];
  notes?: string;
  assigned_agent_id?: string;
  tags?: string[];
}

export const leadsService = {
  async getLeads(): Promise<Lead[] | null> {
    const response = await apiService.get<Lead[]>('/leads');
    return response.data || null;
  },

  async getLead(id: number): Promise<Lead | null> {
    const response = await apiService.get<Lead>(`/leads/${id}`);
    return response.data || null;
  },

  async createLead(leadData: CreateLeadRequest): Promise<Lead | null> {
    const response = await apiService.post<Lead>('/leads', leadData);
    return response.data || null;
  },

  async updateLead(id: number, leadData: UpdateLeadRequest): Promise<Lead | null> {
    const response = await apiService.put<Lead>(`/leads/${id}`, leadData);
    return response.data || null;
  },

  async deleteLead(id: number): Promise<boolean> {
    const response = await apiService.delete(`/leads/${id}`);
    return response.status === 200;
  },

  async searchLeads(query: string): Promise<Lead[] | null> {
    const response = await apiService.get<Lead[]>(`/leads/search?q=${encodeURIComponent(query)}`);
    return response.data || null;
  },

  async getLeadsWithFilters(filters: {
    stage?: string;
    classification?: string;
    assigned_agent?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<Lead[] | null> {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const response = await apiService.get<Lead[]>(`/leads?${params.toString()}`);
    return response.data || null;
  },
};