import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, FormControl, InputLabel, MenuItem, Select, Typography } from '@mui/material';
import { ChartSeries } from '../services/api';

interface LabChartProps {
  chartSeries: ChartSeries[];
}

const LabChart: React.FC<LabChartProps> = ({ chartSeries }) => {
  const [selectedTest, setSelectedTest] = useState<string>(
    chartSeries.length > 0 ? chartSeries[0].test_name : ''
  );

  if (chartSeries.length === 0) {
    return <Typography>No chart data available</Typography>;
  }

  const selectedSeries = chartSeries.find((s) => s.test_name === selectedTest);
  if (!selectedSeries) {
    return <Typography>No data for selected test</Typography>;
  }

  const chartData = selectedSeries.points.map((point) => {
    // Remove seconds from timestamp: "d.m.yyyy HH:MM:SS" -> "d.m.yyyy HH:MM"
    const formattedTimestamp = point.timestamp 
      ? point.timestamp.replace(/(\d{2}:\d{2}):\d{2}/, '$1') 
      : point.timestamp;
    return {
      timestamp: point.timestamp,
      formattedTimestamp,
      value: point.value,
      status: point.result_status,
    };
  });

  return (
    <Box>
      <FormControl sx={{ minWidth: 200, mb: 2 }}>
        <InputLabel>Test Name</InputLabel>
        <Select value={selectedTest} label="Test Name" onChange={(e) => setSelectedTest(e.target.value)}>
          {chartSeries.map((series) => (
            <MenuItem key={series.test_name} value={series.test_name}>
              {series.test_name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="formattedTimestamp" 
            angle={-45} 
            textAnchor="end" 
            height={100}
            tickFormatter={(value) => {
              if (!value) return '';
              return String(value).replace(/(\d{2}:\d{2}):\d{2}/, '$1');
            }}
          />
          <YAxis 
            tickFormatter={(value) => {
              if (value === null || value === undefined) return '';
              return typeof value === 'number' ? value.toFixed(2) : String(value);
            }}
          />
          <Tooltip 
            formatter={(value: any) => {
              if (value === null || value === undefined) return 'N/A';
              return typeof value === 'number' ? value.toFixed(2) : String(value);
            }}
            labelFormatter={(label) => {
              if (!label) return '';
              return String(label).replace(/(\d{2}:\d{2}):\d{2}/, '$1');
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#8884d8" name="Value" />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default LabChart;

