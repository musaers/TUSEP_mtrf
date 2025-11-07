import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Plus, Clock, CheckCircle, Play, Square } from 'lucide-react';

const Faults = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [faults, setFaults] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFault, setSelectedFault] = useState(null);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showRepairDialog, setShowRepairDialog] = useState(false);
  const [assignTo, setAssignTo] = useState('');
  const [repairNotes, setRepairNotes] = useState('');
  const [repairCategory, setRepairCategory] = useState('');

  useEffect(() => {
    fetchFaults();
    if (user?.role === 'manager') {
      fetchTechnicians();
    }
  }, []);

  const fetchFaults = async () => {
    try {
      let response;
      if (user?.role === 'manager' || user?.role === 'quality') {
        response = await axios.get(`${API}/faults/all`);
      } else {
        response = await axios.get(`${API}/faults`);
      }
      setFaults(response.data);
    } catch (error) {
      toast.error('Arızalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchTechnicians = async () => {
    try {
      const response = await axios.get(`${API}/users/technicians`);
      setTechnicians(response.data);
    } catch (error) {
      console.error('Failed to fetch technicians', error);
    }
  };

  const handleAssign = async () => {
    if (!assignTo || !selectedFault) return;
    try {
      await axios.post(`${API}/faults/${selectedFault.id}/assign`, { assigned_to: assignTo });
      toast.success('Arıza atandı');
      setShowAssignDialog(false);
      setAssignTo('');
      fetchFaults();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Atama başarısız');
    }
  };

  const handleStartRepair = async (faultId) => {
    try {
      await axios.post(`${API}/faults/${faultId}/start-repair`);
      toast.success('Onarım başlatıldı');
      fetchFaults();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Onarım başlatılamadı');
    }
  };

  const handleEndRepair = async () => {
    if (!repairNotes || !selectedFault || !repairCategory) {
      toast.error('Lütfen tüm alanları doldurun');
      return;
    }
    
    if (repairNotes.length < 20) {
      toast.error('Onarım notları en az 20 karakter olmalıdır');
      return;
    }
    
    try {
      await axios.post(`${API}/faults/${selectedFault.id}/end-repair`, { 
        repair_notes: repairNotes,
        repair_category: repairCategory 
      });
      toast.success('Onarım tamamlandı');
      setShowRepairDialog(false);
      setRepairNotes('');
      setRepairCategory('');
      fetchFaults();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Onarım tamamlanamadı');
    }
  };

  const handleConfirm = async (faultId) => {
    try {
      await axios.post(`${API}/faults/${faultId}/confirm`);
      toast.success('Onarım onaylandı');
      fetchFaults();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Onaylama başarısız');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'open': { label: 'Açık', class: 'status-open' },
      'in_progress': { label: 'Devam Ediyor', class: 'status-in-progress' },
      'closed': { label: 'Kapatıldı', class: 'status-closed' }
    };
    const config = statusMap[status] || statusMap['open'];
    return <span className={`status-badge ${config.class}`}>{config.label}</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="faults-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Arıza Kayıtları</h1>
          <p className="text-gray-600">Tıbbi cihaz arıza ve onarım takibi</p>
        </div>
        {user?.role === 'health_staff' && (
          <Button onClick={() => navigate('/faults/create')} data-testid="create-fault-btn">
            <Plus className="w-4 h-4 mr-2" />
            Arıza Bildir
          </Button>
        )}
      </div>

      {/* Faults Table */}
      <Card className="glass-card">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Açıklama</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Oluşturan</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Teknisyen</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Durum</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {faults.map((fault) => (
                  <tr key={fault.id} className="border-b hover:bg-gray-50" data-testid={`fault-row-${fault.id}`}>
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium text-gray-900">{fault.device_code}</div>
                        <div className="text-sm text-gray-600">{fault.device_type}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm max-w-xs truncate">{fault.description}</td>
                    <td className="py-3 px-4 text-sm">{fault.created_by_name}</td>
                    <td className="py-3 px-4 text-sm">{fault.assigned_to_name || '-'}</td>
                    <td className="py-3 px-4">{getStatusBadge(fault.status)}</td>
                    <td className="py-3 px-4 text-sm">
                      {new Date(fault.created_at).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {/* Manager: Assign */}
                        {user?.role === 'manager' && fault.status === 'open' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedFault(fault);
                              setShowAssignDialog(true);
                            }}
                            data-testid={`assign-btn-${fault.id}`}
                          >
                            Ata
                          </Button>
                        )}

                        {/* Technician: Start/End Repair */}
                        {user?.role === 'technician' && fault.assigned_to === user.id && (
                          <>
                            {fault.status === 'in_progress' && !fault.repair_start && (
                              <Button
                                size="sm"
                                onClick={() => handleStartRepair(fault.id)}
                                data-testid={`start-repair-btn-${fault.id}`}
                              >
                                <Play className="w-4 h-4 mr-1" />
                                Başlat
                              </Button>
                            )}
                            {fault.repair_start && !fault.repair_end && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedFault(fault);
                                  setShowRepairDialog(true);
                                }}
                                data-testid={`end-repair-btn-${fault.id}`}
                              >
                                <Square className="w-4 h-4 mr-1" />
                                Bitir
                              </Button>
                            )}
                          </>
                        )}

                        {/* Health Staff: Confirm */}
                        {user?.role === 'health_staff' &&
                          fault.created_by === user.id &&
                          fault.repair_end &&
                          fault.status !== 'closed' && (
                            <Button
                              size="sm"
                              onClick={() => handleConfirm(fault.id)}
                              data-testid={`confirm-btn-${fault.id}`}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Onayla
                            </Button>
                          )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {faults.length === 0 && (
            <div className="text-center py-12 text-gray-600">
              Arıza kaydı bulunamadı
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Teknisyen Ata</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Teknisyen Seç</Label>
              <Select value={assignTo} onValueChange={setAssignTo}>
                <SelectTrigger data-testid="assign-technician-select">
                  <SelectValue placeholder="Teknisyen seçin" />
                </SelectTrigger>
                <SelectContent>
                  {technicians.map((tech) => (
                    <SelectItem key={tech.id} value={tech.id}>
                      {tech.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleAssign} className="w-full" disabled={!assignTo} data-testid="confirm-assign-btn">
              Ata
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* End Repair Dialog */}
      <Dialog open={showRepairDialog} onOpenChange={setShowRepairDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Onarımı Tamamla</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="repair-notes">Onarım Notları</Label>
              <Textarea
                id="repair-notes"
                data-testid="repair-notes-input"
                placeholder="Yapılan işlemler, değiştirilen parçalar vb."
                value={repairNotes}
                onChange={(e) => setRepairNotes(e.target.value)}
                rows={4}
              />
            </div>
            <Button onClick={handleEndRepair} className="w-full" disabled={!repairNotes} data-testid="confirm-end-repair-btn">
              Tamamla
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Faults;