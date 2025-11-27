import axios from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PatientMonitoringItem {
  patient_id: number;
  case_number: number;
  name: string;
  age: number | null;
  department: string | null;
  room_number: string | null;
  admission_datetime: string | null;
  admission_length: string;
  last_test_datetime: string | null;
  time_since_last_test: string | null;
  last_test_name: string | null;
  primary_physician: string | null;
  needs_alert: boolean;
}

export interface PatientMonitoringResponse {
  data: PatientMonitoringItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

export interface LabResultItem {
  test_name: string;
  order_date: string | null;
  order_time: string | null;
  ordering_physician: string | null;
  result_value: number | null;
  result_unit: string | null;
  reference_range: string | null;
  result_status: string | null;
  performed_date: string | null;
  performed_time: string | null;
  reviewing_physician: string | null;
}

export interface ChartPoint {
  timestamp: string;
  value: number | null;
  result_status: string | null;
}

export interface ChartSeries {
  test_name: string;
  points: ChartPoint[];
}

export interface LastTestSummary {
  test_name: string;
  last_test_datetime: string;
  hours_since_last_test: number | null;
}

export interface PatientDetailResponse {
  patient_id: number;
  name: string;
  age: number | null;
  primary_physician: string | null;
  insurance_provider: string | null;
  blood_type: string | null;
  allergies: string | null;
  department: string | null;
  room_number: string | null;
  admission_datetime: string | null;
  hours_since_admission: number | null;
  last_test: LastTestSummary | null;
  latest_results: LabResultItem[];
  chart_series: ChartSeries[];
}

export const patientApi = {
  getMonitoring: async (
    hoursThreshold: number = 48,
    department?: string,
    page: number = 1,
    limit: number = 50
  ): Promise<PatientMonitoringResponse> => {
    const params = new URLSearchParams({
      hours_threshold: hoursThreshold.toString(),
      page: page.toString(),
      limit: limit.toString(),
    });
    if (department) {
      params.append('department', department);
    }
    const response = await apiClient.get<PatientMonitoringResponse>(
      `/patients/monitoring?${params.toString()}`
    );
    return response.data;
  },

  getPatientDetail: async (patientId: number): Promise<PatientDetailResponse> => {
    const response = await apiClient.get<PatientDetailResponse>(`/patients/${patientId}`);
    return response.data;
  },
};

