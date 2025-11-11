import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { ArrowLeft, AlertCircle } from 'lucide-react';

const CreateFault = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [allDevices, setAllDevices] = useState([]);
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    device_id: '',
    description: ''
  });
  const [filters, setFilters] = useState({
    device_id: '',
    type: '',
    location: ''
  });

  useEffect(() => {
    fetchDevices();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [filters, allDevices]);

  const fetchDevices = async () => {
    try {
      const response = await axios.get(`${API}/devices`);
      setAllDevices(response.data);
      setDevices(response.data);
      
      // Extract unique types and locations
      const types = [...new Set(response.data.map(d => d.type))];
      const locs = [...new Set(response.data.map(d => d.location))];
      setDeviceTypes(types);
      setLocations(locs);
    } catch (error) {
      toast.error('Cihazlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allDevices];
    
    if (filters.device_id) {
      filtered = filtered.filter(d => d.id.toLowerCase().includes(filters.device_id.toLowerCase()));
    }
    if (filters.type) {
      filtered = filtered.filter(d => d.type === filters.type);
    }
    if (filters.location) {
      filtered = filtered.filter(d => d.location === filters.location);
    }
    
    setDevices(filtered);
  };

  const resetFilters = () => {
    setFilters({
      device_id: '',
      type: '',
      location: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API}/faults`, formData);
      toast.success('Arıza başarıyla bildirildi');
      navigate('/faults');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Arıza bildirilemedi');
    } finally {
      setSubmitting(false);
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
    <div className="max-w-2xl mx-auto space-y-6" data-testid="create-fault-page">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/faults')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Geri
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Arıza Bildir</h1>
          <p className="text-gray-600">Yeni arıza kaydı oluştur</p>
        </div>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <CardTitle>Arıza Bildir</CardTitle>
              <p className="text-sm text-gray-600 mt-1">Lütfen arızalı cihazı ve sorunu detaylı açıklayın</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="device">Cihaz *</Label>
              <Select
                value={formData.device_id}
                onValueChange={(value) => setFormData({ ...formData, device_id: value })}
                required
              >
                <SelectTrigger data-testid="device-select">
                  <SelectValue placeholder="Cihaz seçin" />
                </SelectTrigger>
                <SelectContent>
                  {devices.map((device) => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.code} - {device.type} ({device.location})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-600">Arızalı cihazın kodunu barkod/QR ile okutabilir veya listeden seçebilirsiniz</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Arıza Açıklaması *</Label>
              <Textarea
                id="description"
                data-testid="description-input"
                placeholder="Arızanın detaylı açıklamasını yazın (belirti, ne zaman başladı, nasıl oluştu vb.)"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={6}
                required
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">Bilgi</h4>
              <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                <li>Arıza bildirimi oluşturulduktan sonra Teknik Servis Departmanı'na otomatik bildirim gönderilir</li>
                <li>Teknik Yönetici bir teknisyen atayacaktır</li>
                <li>Onarım tamamlandıktan sonra onaylaymanız istenecektir</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => navigate('/faults')}
              >
                İptal
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={submitting || !formData.device_id || !formData.description}
                data-testid="submit-fault-btn"
              >
                {submitting ? 'Gönderiliyor...' : 'Arıza Bildir'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateFault;