import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Search, Activity } from 'lucide-react';

const Devices = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [filteredDevices, setFilteredDevices] = useState([]);
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newDevice, setNewDevice] = useState({
    type: '',
    location: '',
    total_operating_hours: 8760
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
    const filtered = devices.filter(device =>
      device.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.location.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredDevices(filtered);
  }, [searchTerm, devices]);

  const fetchDevices = async () => {
    try {
      const response = await axios.get(`${API}/devices`);
      setDevices(response.data);
      setFilteredDevices(response.data);
    } catch (error) {
      toast.error('Cihazlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleAddDevice = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/devices`, newDevice);
      toast.success('Cihaz başarıyla eklendi');
      setShowAddDialog(false);
      setNewDevice({ code: '', type: '', location: '', total_operating_hours: 8760 });
      fetchDevices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Cihaz eklenemedi');
    }
  };

  const getAvailabilityColor = (availability) => {
    if (availability >= 95) return 'text-green-600';
    if (availability >= 85) return 'text-amber-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="devices-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Cihazlar</h1>
          <p className="text-gray-600">Tıbbi cihaz envanteri ve performans metrikleri</p>
        </div>
        {(user?.role === 'manager' || user?.role === 'technician') && (
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button data-testid="add-device-btn">
                <Plus className="w-4 h-4 mr-2" />
                Cihaz Ekle
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Yeni Cihaz Ekle</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddDevice} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Cihaz Kodu</Label>
                  <Input
                    id="code"
                    data-testid="device-code-input"
                    placeholder="örn: CIH-001"
                    value={newDevice.code}
                    onChange={(e) => setNewDevice({ ...newDevice, code: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Cihaz Tipi</Label>
                  <Input
                    id="type"
                    data-testid="device-type-input"
                    placeholder="örn: MR Cihazı"
                    value={newDevice.type}
                    onChange={(e) => setNewDevice({ ...newDevice, type: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Konum</Label>
                  <Input
                    id="location"
                    data-testid="device-location-input"
                    placeholder="örn: Radyoloji Bölümü"
                    value={newDevice.location}
                    onChange={(e) => setNewDevice({ ...newDevice, location: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="operating-hours">Toplam Çalışma Saati</Label>
                  <Input
                    id="operating-hours"
                    data-testid="device-operating-hours-input"
                    type="number"
                    value={newDevice.total_operating_hours}
                    onChange={(e) => setNewDevice({ ...newDevice, total_operating_hours: parseFloat(e.target.value) })}
                    required
                  />
                </div>
                <Button type="submit" className="w-full" data-testid="submit-device-btn">
                  Ekle
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <Input
          placeholder="Cihaz kodu, tipi veya konum ile ara..."
          className="pl-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          data-testid="search-devices-input"
        />
      </div>

      {/* Devices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDevices.map((device) => (
          <Card
            key={device.id}
            className="metric-card cursor-pointer hover:shadow-lg"
            onClick={() => navigate(`/devices/${device.id}`)}
            data-testid={`device-card-${device.code}`}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{device.code}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">{device.type}</p>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Activity className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Konum:</span>
                  <span className="text-sm font-medium">{device.location}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Arıza Sayısı:</span>
                  <span className="text-sm font-medium">{device.total_failures}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">MTBF:</span>
                  <span className="text-sm font-medium">{device.mtbf.toFixed(1)} saat</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">MTTR:</span>
                  <span className="text-sm font-medium">{device.mttr.toFixed(1)} saat</span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="text-sm text-gray-600">Kullanılabilirlik:</span>
                  <span className={`text-lg font-bold ${getAvailabilityColor(device.availability)}`}>
                    {device.availability.toFixed(2)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredDevices.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">Cihaz bulunamadı</p>
        </div>
      )}
    </div>
  );
};

export default Devices;