import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { FileText, TrendingUp, Clock, Users } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Reports = () => {
  const { user } = useContext(AuthContext);
  const [breakdownReport, setBreakdownReport] = useState([]);
  const [interventionReport, setInterventionReport] = useState([]);
  const [technicianReport, setTechnicianReport] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const [breakdown, intervention, technician] = await Promise.all([
        axios.get(`${API}/reports/breakdown-frequency`),
        axios.get(`${API}/reports/intervention-duration`),
        axios.get(`${API}/reports/technician-performance`)
      ]);
      setBreakdownReport(breakdown.data);
      setInterventionReport(intervention.data);
      setTechnicianReport(technician.data);
    } catch (error) {
      toast.error('Raporlar yüklenemedi');
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

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">TÜSEP Raporları</h1>
        <p className="text-gray-600">Kalite göstergeleri ve performans raporları</p>
      </div>

      <Tabs defaultValue="breakdown" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="breakdown" data-testid="breakdown-tab">
            <FileText className="w-4 h-4 mr-2" />
            Arızalanma Sıklığı
          </TabsTrigger>
          <TabsTrigger value="intervention" data-testid="intervention-tab">
            <Clock className="w-4 h-4 mr-2" />
            Müdahale Süresi
          </TabsTrigger>
          <TabsTrigger value="technician" data-testid="technician-tab">
            <Users className="w-4 h-4 mr-2" />
            Teknisyen Performansı
          </TabsTrigger>
        </TabsList>

        {/* Breakdown Frequency Report (Gİ.YD.DH.08) */}
        <TabsContent value="breakdown" className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Gİ.YD.DH.08 - Cihaz Arızalanma Sıklığı Göstergesi</CardTitle>
              <p className="text-sm text-gray-600 mt-2">
                Cihazların arıza sıklığını gösterir. Yüksek değerler daha az arıza anlamına gelir.
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz Kodu</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz Tipi</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Konum</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Arıza Sayısı</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Çalışma Saati</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Arıza Sıklığı</th>
                    </tr>
                  </thead>
                  <tbody>
                    {breakdownReport.map((item, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium">{item.device_code}</td>
                        <td className="py-3 px-4 text-sm">{item.device_type}</td>
                        <td className="py-3 px-4 text-sm">{item.location}</td>
                        <td className="py-3 px-4 text-sm text-right">{item.total_failures}</td>
                        <td className="py-3 px-4 text-sm text-right">{item.operating_hours.toFixed(1)}</td>
                        <td className="py-3 px-4 text-sm text-right font-semibold">
                          {item.breakdown_frequency > 0 ? item.breakdown_frequency.toFixed(2) : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {breakdownReport.length === 0 && (
                <div className="text-center py-8 text-gray-600">Henüz veri bulunmuyor</div>
              )}
            </CardContent>
          </Card>

          {breakdownReport.length > 0 && (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Arızalanma Sıklığı Grafiği</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={breakdownReport.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="device_code" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="total_failures" fill="#ef4444" name="Arıza Sayısı" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Intervention Duration Report (Gİ.YD.DH.07) */}
        <TabsContent value="intervention" className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Gİ.YD.DH.07 - Cihaz Arızalarına Müdahale Süresi Göstergesi</CardTitle>
              <p className="text-sm text-gray-600 mt-2">
                Arıza bildirimi ile onarım tamamlanması arasındaki ortalama süre. Hedef: En az sürede müdahale.
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz Kodu</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz Tipi</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Toplam Müdahale</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Ortalama Süre (saat)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {interventionReport.map((item, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium">{item.device_code}</td>
                        <td className="py-3 px-4 text-sm">{item.device_type}</td>
                        <td className="py-3 px-4 text-sm text-right">{item.total_interventions}</td>
                        <td className="py-3 px-4 text-sm text-right font-semibold">
                          <span className={item.average_duration_hours > 24 ? 'text-red-600' : 'text-green-600'}>
                            {item.average_duration_hours.toFixed(2)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {interventionReport.length === 0 && (
                <div className="text-center py-8 text-gray-600">Henüz veri bulunmuyor</div>
              )}
            </CardContent>
          </Card>

          {interventionReport.length > 0 && (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Ortalama Müdahale Süresi Grafiği</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={interventionReport.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="device_code" />
                      <YAxis label={{ value: 'Saat', angle: -90, position: 'insideLeft' }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="average_duration_hours" fill="#f59e0b" name="Ortalama Süre (saat)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Technician Performance Report */}
        <TabsContent value="technician" className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Teknisyen Performans Raporu</CardTitle>
              <p className="text-sm text-gray-600 mt-2">
                Teknisyenlerin atanan iş sayısı ve başarı oranları.
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Teknisyen</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">E-posta</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Atanan</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Tamamlanan</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Başarı Oranı</th>
                    </tr>
                  </thead>
                  <tbody>
                    {technicianReport.map((tech, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium">{tech.name}</td>
                        <td className="py-3 px-4 text-sm">{tech.email}</td>
                        <td className="py-3 px-4 text-sm text-right">{tech.total_assigned}</td>
                        <td className="py-3 px-4 text-sm text-right">{tech.completed}</td>
                        <td className="py-3 px-4 text-sm text-right">
                          <span className={`font-semibold ${
                            tech.success_rate >= 90 ? 'text-green-600' :
                            tech.success_rate >= 70 ? 'text-amber-600' : 'text-red-600'
                          }`}>
                            {tech.success_rate.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {technicianReport.length === 0 && (
                <div className="text-center py-8 text-gray-600">Henüz veri bulunmuyor</div>
              )}
            </CardContent>
          </Card>

          {technicianReport.length > 0 && (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Teknisyen Başarı Oranları</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={technicianReport}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="success_rate" fill="#10b981" name="Başarı Oranı (%)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;