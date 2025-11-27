import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Grid,
  Chip,
  AppBar,
  Toolbar,
  Switch,
  IconButton,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import PersonIcon from '@mui/icons-material/Person';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ScienceIcon from '@mui/icons-material/Science';
import PersonPinIcon from '@mui/icons-material/PersonPin';
import BadgeIcon from '@mui/icons-material/Badge';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import BloodtypeIcon from '@mui/icons-material/Bloodtype';
import WarningIcon from '@mui/icons-material/Warning';
import { patientApi, PatientDetailResponse } from '../services/api';
import LabChart from '../components/LabChart';

interface PatientDetailProps {
  mode: 'light' | 'dark';
  setMode: (mode: 'light' | 'dark') => void;
}

const PatientDetail: React.FC<PatientDetailProps> = ({ mode, setMode }) => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<PatientDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const formatDateTime = (dateTime: string | null | undefined): string => {
    if (!dateTime) return 'N/A';
    return dateTime.replace(/:\d{2}$/, '');
  };

  useEffect(() => {
    if (!patientId) return;
    const fetchPatient = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await patientApi.getPatientDetail(parseInt(patientId, 10));
        setPatient(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch patient details');
      } finally {
        setLoading(false);
      }
    };
    fetchPatient();
  }, [patientId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !patient) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Patient not found'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <AppBar position="static" elevation={0} sx={{ bgcolor: 'primary.main', mb: 3 }}>
        <Toolbar>
          <IconButton 
            onClick={() => navigate('/')} 
            sx={{ color: 'white', mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 600, color: 'white' }}>
            Patient Details
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Brightness7Icon sx={{ color: 'white' }} />
            <Switch
              checked={mode === 'dark'}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMode(e.target.checked ? 'dark' : 'light')}
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: 'white',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: 'rgba(255, 255, 255, 0.5)',
                },
              }}
            />
            <Brightness4Icon sx={{ color: 'white' }} />
            <Typography sx={{ color: 'white', ml: 1 }}>
              {mode === 'dark' ? 'Dark' : 'Light'} Mode
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        {patient.name}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Patient Information
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(7, 1fr)',
                  gap: 2,
                  '@media (max-width: 1200px)': {
                    gridTemplateColumns: 'repeat(4, 1fr)',
                  },
                  '@media (max-width: 768px)': {
                    gridTemplateColumns: 'repeat(2, 1fr)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BadgeIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Patient ID</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.patient_id}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Name</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.name}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarTodayIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Age</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.age !== null ? patient.age : 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocalHospitalIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Department</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.department || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MeetingRoomIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Room</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.room_number || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccessTimeIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Admission Datetime</Typography>
                    <Typography variant="body2" fontWeight="medium">{formatDateTime(patient.admission_datetime)}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccessTimeIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Admission Length</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {patient.hours_since_admission !== null
                        ? `${patient.hours_since_admission.toFixed(1)}h`
                        : 'N/A'}
                    </Typography>
                  </Box>
                </Box>
                {patient.last_test ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AccessTimeIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Last Test Datetime</Typography>
                        <Typography variant="body2" fontWeight="medium">{formatDateTime(patient.last_test.last_test_datetime)}</Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AccessTimeIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Time Since Last Test</Typography>
                        <Typography variant="body2" fontWeight="medium">
                          {patient.last_test.hours_since_last_test !== null
                            ? `${patient.last_test.hours_since_last_test.toFixed(1)}h`
                            : 'N/A'}
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ScienceIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Last Test</Typography>
                        <Typography variant="body2" fontWeight="medium">{patient.last_test.test_name}</Typography>
                      </Box>
                    </Box>
                  </>
                ) : (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AccessTimeIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Last Test Datetime</Typography>
                        <Typography variant="body2" fontWeight="medium">N/A</Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AccessTimeIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Time Since Last Test</Typography>
                        <Typography variant="body2" fontWeight="medium">N/A</Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ScienceIcon color="primary" fontSize="small" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">Last Test</Typography>
                        <Typography variant="body2" fontWeight="medium">N/A</Typography>
                      </Box>
                    </Box>
                  </>
                )}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonPinIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Primary Physician</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.primary_physician || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HealthAndSafetyIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Insurance Provider</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.insurance_provider || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BloodtypeIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Blood Type</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.blood_type || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Allergies</Typography>
                    <Typography variant="body2" fontWeight="medium">{patient.allergies || 'None'}</Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Latest Lab Results
              </Typography>
              <TableContainer component={Paper} sx={{ flexGrow: 1, maxHeight: 400 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Test Name</TableCell>
                      <TableCell>Value</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Order Date/Time</TableCell>
                      <TableCell>Performed Date/Time</TableCell>
                      <TableCell>Ordering Physician</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {patient.latest_results.map((result, idx) => {
                      const formatDateTime = (date: string | null | undefined, time: string | null | undefined): string => {
                        if (!date) return 'N/A';
                        // Remove seconds if present
                        const datePart = date.split(' ')[0];
                        const timePart = time ? time.split(':').slice(0, 2).join(':') : '';
                        if (timePart) {
                          return `${datePart} ${timePart}`;
                        }
                        return datePart;
                      };
                      const performedDateTime = formatDateTime(result.performed_date, result.performed_time);
                      const orderDateTime = formatDateTime(result.order_date, result.order_time);
                      const value = result.result_value !== null 
                        ? (typeof result.result_value === 'number' 
                            ? result.result_value.toFixed(2) 
                            : parseFloat(String(result.result_value)).toFixed(2))
                        : 'N/A';
                      return (
                        <TableRow key={idx}>
                          <TableCell>{result.test_name}</TableCell>
                          <TableCell>
                            {value !== 'N/A' 
                              ? `${value}${result.result_unit ? ` ${result.result_unit}` : ''}` 
                              : 'N/A'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={result.result_status || 'N/A'}
                              color={
                                result.result_status === 'Normal'
                                  ? 'success'
                                  : result.result_status?.includes('Abnormal')
                                  ? 'error'
                                  : 'default'
                              }
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{orderDateTime}</TableCell>
                          <TableCell>{performedDateTime}</TableCell>
                          <TableCell>{result.ordering_physician || 'N/A'}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Lab Results Over Time
              </Typography>
              <Box sx={{ flexGrow: 1 }}>
                <LabChart chartSeries={patient.chart_series} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
    </Box>
  );
};

export default PatientDetail;

