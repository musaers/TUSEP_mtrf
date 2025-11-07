import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Activity, AlertCircle, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { formatTimeMinutesSeconds } from '../utils/timeFormat';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats', error);
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

  const reliabilityData = stats?.most_reliable_devices?.slice(0, 5).map(d => ({
    name: d.code,
    availability: d.availability,
    mtbf: d.mtbf
  })) || [];

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Gösterge Paneli</h1>
        <p className="text-gray-600">Hoş geldiniz, {user?.name}</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="metric-card" data-testid="total-devices-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Toplam Cihaz</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_devices || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card" data-testid="open-faults-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Açık Arızalar</p>
                <p className="text-3xl font-bold text-amber-600">{stats?.open_faults || 0}</p>
              </div>
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card" data-testid="in-progress-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Devam Eden</p>
                <p className="text-3xl font-bold text-blue-600">{stats?.in_progress_faults || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card" data-testid="closed-faults-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Tamamlanan</p>
                <p className="text-3xl font-bold text-green-600">{stats?.closed_faults || 0}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* MTBF, MTTR, Availability */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">Ortalama MTBF</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{stats?.avg_mtbf || 0} <span className="text-lg text-gray-600">saat</span></div>
            <p className="text-sm text-gray-600 mt-2">Arızalar arası ortalama süre</p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">Ortalama MTTR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{stats?.avg_mttr || 0} <span className="text-lg text-gray-600">saat</span></div>
            <p className="text-sm text-gray-600 mt-2">Ortalama onarım süresi</p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">Ortalama Kullanılabilirlik</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{stats?.avg_availability?.toFixed(2) || 100}%</div>
            <p className="text-sm text-gray-600 mt-2">Cihaz kullanılabilirlik oranı</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      {reliabilityData.length > 0 && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>En Güvenilir Cihazlar</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={reliabilityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="availability" fill="#3b82f6" name="Kullanılabilirlik (%)" />
                  <Bar dataKey="mtbf" fill="#10b981" name="MTBF (saat)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Role-specific quick actions */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Hızlı İşlemler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {user?.role === 'health_staff' && (
              <a href="/faults/create" className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
                <AlertCircle className="w-8 h-8 text-blue-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Arıza Bildir</h3>
                <p className="text-sm text-gray-600">Yeni arıza kaydı oluştur</p>
              </a>
            )}
            {user?.role === 'technician' && (
              <a href="/faults" className="p-4 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors">
                <Clock className="w-8 h-8 text-amber-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Bekleyen İşler</h3>
                <p className="text-sm text-gray-600">Atanan arızaları görüntüle</p>
              </a>
            )}
            {(user?.role === 'manager' || user?.role === 'quality') && (
              <a href="/reports" className="p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                <TrendingUp className="w-8 h-8 text-green-600 mb-2" />
                <h3 className="font-semibold text-gray-900">Raporlar</h3>
                <p className="text-sm text-gray-600">TÜSEP uyumluluk raporları</p>
              </a>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;