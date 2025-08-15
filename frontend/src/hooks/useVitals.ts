import { useState, useEffect } from 'react';
import { api, endpoints } from '../lib/api';
import toast from 'react-hot-toast';

interface VitalRecord {
  id: number;
  category: {
    id: number;
    name: string;
    unit: string;
    normal_range_min?: number;
    normal_range_max?: number;
  };
  value: number;
  recorded_at: string;
  notes?: string;
}

interface VitalCategory {
  id: number;
  name: string;
  unit: string;
  normal_range_min?: number;
  normal_range_max?: number;
  description?: string;
}

interface VitalGoal {
  id: number;
  category: VitalCategory;
  target_value: number;
  target_date: string;
  current_value?: number;
  progress_percentage?: number;
}

export const useVitals = () => {
  const [vitalRecords, setVitalRecords] = useState<VitalRecord[]>([]);
  const [categories, setCategories] = useState<VitalCategory[]>([]);
  const [goals, setGoals] = useState<VitalGoal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVitalRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoints.vitals);
      setVitalRecords(response.data);
    } catch (error: any) {
      console.error('Error fetching vital records:', error);
      setError(error.response?.data?.message || 'Failed to fetch vital records');
      toast.error('Failed to fetch vital records');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get(`${endpoints.vitals}categories/`);
      setCategories(response.data);
    } catch (error: any) {
      console.error('Error fetching vital categories:', error);
    }
  };

  const fetchGoals = async () => {
    try {
      const response = await api.get(`${endpoints.vitals}goals/`);
      setGoals(response.data);
    } catch (error: any) {
      console.error('Error fetching vital goals:', error);
    }
  };

  const addVitalRecord = async (data: { category_id: number; value: number; notes?: string }): Promise<boolean> => {
    try {
      setLoading(true);
      await api.post(endpoints.vitals, data);
      await fetchVitalRecords();
      toast.success('Vital record added successfully!');
      return true;
    } catch (error: any) {
      console.error('Error adding vital record:', error);
      const message = error.response?.data?.message || 'Failed to add vital record';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getLatestVitals = () => {
    const latestVitals: { [key: string]: VitalRecord } = {};
    
    vitalRecords.forEach(record => {
      const categoryName = record.category.name;
      if (!latestVitals[categoryName] || 
          new Date(record.recorded_at) > new Date(latestVitals[categoryName].recorded_at)) {
        latestVitals[categoryName] = record;
      }
    });
    
    return Object.values(latestVitals);
  };

  const getVitalHistory = (categoryId: number) => {
    return vitalRecords
      .filter(record => record.category.id === categoryId)
      .sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime());
  };

  const getVitalTrends = () => {
    const trends: { [key: string]: { values: number[]; dates: string[] } } = {};
    
    vitalRecords.forEach(record => {
      const categoryName = record.category.name;
      if (!trends[categoryName]) {
        trends[categoryName] = { values: [], dates: [] };
      }
      trends[categoryName].values.push(record.value);
      trends[categoryName].dates.push(record.recorded_at);
    });
    
    return trends;
  };

  const getHealthAssessment = () => {
    const latestVitals = getLatestVitals();
    let riskLevel = 'Low';
    let issues: string[] = [];
    
    latestVitals.forEach(vital => {
      const { normal_range_min, normal_range_max } = vital.category;
      if (normal_range_min !== undefined && normal_range_max !== undefined) {
        if (vital.value < normal_range_min || vital.value > normal_range_max) {
          issues.push(`${vital.category.name} is outside normal range`);
          if (riskLevel === 'Low') riskLevel = 'Medium';
        }
      }
    });
    
    if (issues.length > 2) {
      riskLevel = 'High';
    }
    
    return {
      riskLevel,
      issues,
      lastAssessment: new Date().toISOString(),
    };
  };

  useEffect(() => {
    fetchVitalRecords();
    fetchCategories();
    fetchGoals();
  }, []);

  return {
    vitalRecords,
    categories,
    goals,
    loading,
    error,
    fetchVitalRecords,
    addVitalRecord,
    getLatestVitals,
    getVitalHistory,
    getVitalTrends,
    getHealthAssessment,
  };
};
