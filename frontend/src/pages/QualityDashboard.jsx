import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Download, FileText, Activity, Users, AlertCircle, ArrowRightLeft } from 'lucide-react';

const QualityDashboard = () => {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role === 'quality') {
      fetchQualityStats();
      fetchSystemLogs();
    }
  }, [user]);

  const fetchQualityStats = async () => {
    try {
      const response = await axios.get(`${API}/quality/system-stats`);
      setStats(response.data);
    } catch (error) {
      toast.error('İstatistikler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemLogs = async () => {
    try {
      const response = await axios.get(`${API}/quality/all-logs`);
      setLogs(response.data);
    } catch (error) {
      console.error('Logs fetch error', error);
    }
  };

  const downloadExcelReport = async (reportType) => {
    try {
      const year = new Date().getFullYear();
      const response = await axios.get(`${API}/reports/excel/${reportType}?year=${year}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_${year}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Rapor indirildi');
    } catch (error) {
      toast.error('Rapor indirilemedi');
    }
  };

  if (user?.role !== 'quality') {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Bu sayfaya erişim yetkiniz yok</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="quality-dashboard">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Kalite Birimi Dashboard</h1>
        <p className="text-gray-600">Sistem geneli izleme ve raporlama</p>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Toplam Kullanıcı</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_users || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Toplam Cihaz</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_devices || 0}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Toplam Arıza</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_faults || 0}</p>
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
                <p className="text-sm text-gray-600 mb-1">Toplam Transfer</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_transfers || 0}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <ArrowRightLeft className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Bekleyen Transfer</p>
                <p className="text-3xl font-bold text-amber-600">{stats?.pending_transfers || 0}</p>
              </div>
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Excel Reports */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            TÜSEP Excel Raporları
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Gİ.YD.DH.08</h3>
              <p className="text-sm text-gray-600 mb-3">Cihaz Arızalanma Sıklığı</p>
              <Button 
                size="sm" 
                onClick={() => downloadExcelReport('device-failure-frequency')}
                data-testid="download-report-1"
              >
                <Download className="w-4 h-4 mr-2" />
                İndir
              </Button>
            </div>

            <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Gİ.YD.DH.07</h3>
              <p className="text-sm text-gray-600 mb-3">Müdahale Süresi</p>
              <Button 
                size="sm" 
                onClick={() => downloadExcelReport('intervention-duration')}
                data-testid="download-report-2"
              >
                <Download className="w-4 h-4 mr-2" />
                İndir
              </Button>
            </div>

            <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Gİ.YD.DH.02</h3>
              <p className="text-sm text-gray-600 mb-3">Tesis Kaynaklı Sorunlar</p>
              <Button 
                size="sm" 
                onClick={() => downloadExcelReport('facility-issues')}
                data-testid="download-report-3"
              >
                <Download className="w-4 h-4 mr-2" />
                İndir
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Logs */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Sistem Aktivite Logları</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Tarih/Saat</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Kullanıcı</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Olay</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50 text-sm">
                    <td className="py-2 px-3">
                      {new Date(log.timestamp).toLocaleString('tr-TR')}
                    </td>
                    <td className="py-2 px-3">{log.user_name || '-'}</td>
                    <td className="py-2 px-3">{log.event}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QualityDashboard;
