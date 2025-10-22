import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API } from '../App';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { ArrowLeft, Activity, AlertCircle, Clock, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DeviceDetails = () => {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  const [faults, setFaults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDeviceDetails();
  }, [deviceId]);

  const fetchDeviceDetails = async () => {
    try {
      const [deviceRes, faultsRes] = await Promise.all([
        axios.get(`${API}/devices/${deviceId}`),
        axios.get(`${API}/devices/${deviceId}/faults`)
      ]);
      setDevice(deviceRes.data);
      setFaults(faultsRes.data);
    } catch (error) {
      toast.error('Cihaz bilgileri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Cihaz bulunamadı</p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      'open': { label: 'Açık', class: 'status-open' },
      'in_progress': { label: 'Devam Ediyor', class: 'status-in-progress' },
      'closed': { label: 'Kapatıldı', class: 'status-closed' }
    };
    const config = statusMap[status] || statusMap['open'];
    return <span className={`status-badge ${config.class}`}>{config.label}</span>;
  };

  const chartData = faults.slice(0, 10).reverse().map((fault, index) => ({
    name: `#${fault.breakdown_iteration}`,
    duration: fault.repair_duration || 0
  }));

  return (
    <div className="space-y-6" data-testid="device-details-page">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/devices')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Geri
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{device.code}</h1>
          <p className="text-gray-600">{device.type} - {device.location}</p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Toplam Arıza</p>
                <p className="text-3xl font-bold text-gray-900">{device.total_failures}</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">MTBF</p>
                <p className="text-2xl font-bold text-blue-600">{device.mtbf.toFixed(1)} <span className="text-sm">saat</span></p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">MTTR</p>
                <p className="text-2xl font-bold text-amber-600">{device.mttr.toFixed(1)} <span className="text-sm">saat</span></p>
              </div>
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Kullanılabilirlik</p>
                <p className="text-2xl font-bold text-green-600">{device.availability.toFixed(2)}%</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Repair Duration Chart */}
      {chartData.length > 0 && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Onarım Süreleri</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Saat', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="duration" stroke="#3b82f6" strokeWidth={2} name="Onarım Süresi (saat)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fault History */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Arıza Geçmişi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Arıza No</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Açıklama</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Teknisyen</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Süre</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Durum</th>
                </tr>
              </thead>
              <tbody>
                {faults.map((fault) => (
                  <tr key={fault.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm">#{fault.breakdown_iteration}</td>
                    <td className="py-3 px-4 text-sm">
                      {new Date(fault.created_at).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="py-3 px-4 text-sm">{fault.description}</td>
                    <td className="py-3 px-4 text-sm">{fault.assigned_to_name || '-'}</td>
                    <td className="py-3 px-4 text-sm">
                      {fault.repair_duration ? `${fault.repair_duration.toFixed(1)} saat` : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm">{getStatusBadge(fault.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {faults.length === 0 && (
            <div className="text-center py-8 text-gray-600">
              Henüz arıza kaydı bulunmuyor
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DeviceDetails;