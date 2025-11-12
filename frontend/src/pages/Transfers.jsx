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
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, ArrowRightLeft, CheckCircle, XCircle, Clock } from 'lucide-react';

const Transfers = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [transfers, setTransfers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [selectedTransfer, setSelectedTransfer] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [newTransfer, setNewTransfer] = useState({
    device_id: '',
    to_location: '',
    reason: ''
  });

  useEffect(() => {
    fetchTransfers();
    fetchDevices();
  }, []);

  const fetchTransfers = async () => {
    try {
      const response = await axios.get(`${API}/transfers`);
      setTransfers(response.data);
    } catch (error) {
      toast.error('Transfer kayıtları yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await axios.get(`${API}/devices`);
      setDevices(response.data);
    } catch (error) {
      console.error('Devices load error', error);
    }
  };

  const handleCreateTransfer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/transfers`, newTransfer);
      toast.success('Transfer talebi oluşturuldu');
      setShowCreateDialog(false);
      setNewTransfer({ device_id: '', to_location: '', reason: '' });
      fetchTransfers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Transfer talebi oluşturulamadı');
    }
  };

  const handleApprove = async (transferId) => {
    try {
      await axios.post(`${API}/transfers/${transferId}/approve`);
      toast.success('Transfer onaylandı');
      fetchTransfers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Transfer onaylanamadı');
    }
  };

  const handleReject = async () => {
    if (!rejectionReason) {
      toast.error('Ret nedeni girilmelidir');
      return;
    }
    
    try {
      await axios.post(`${API}/transfers/${selectedTransfer.id}/reject`, {
        rejection_reason: rejectionReason
      });
      toast.success('Transfer reddedildi');
      setShowRejectDialog(false);
      setRejectionReason('');
      fetchTransfers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Transfer reddedilemedi');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { label: 'Beklemede', class: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'approved': { label: 'Onaylandı', class: 'bg-green-100 text-green-800', icon: CheckCircle },
      'rejected': { label: 'Reddedildi', class: 'bg-red-100 text-red-800', icon: XCircle },
      'completed': { label: 'Tamamlandı', class: 'bg-blue-100 text-blue-800', icon: CheckCircle }
    };
    const config = statusMap[status] || statusMap['pending'];
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${config.class}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="transfers-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Cihaz Transferleri</h1>
          <p className="text-gray-600">Cihaz lokasyon değişikliği yönetimi</p>
        </div>
        {user?.role !== 'quality' && (
          <Button onClick={() => setShowCreateDialog(true)} data-testid="create-transfer-btn">
            <Plus className="w-4 h-4 mr-2" />
            Transfer Talebi Oluştur
          </Button>
        )}
      </div>

      {/* Transfers Table */}
      <Card className="glass-card">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Cihaz</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Kaynak</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Hedef</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Talep Eden</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Sebep</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Durum</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {transfers.map((transfer) => (
                  <tr key={transfer.id} className="border-b hover:bg-gray-50" data-testid={`transfer-row-${transfer.id}`}>
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium text-gray-900">ID: {transfer.device_id}</div>
                        <div className="text-sm text-gray-600">{transfer.device_type}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm">{transfer.from_location}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <ArrowRightLeft className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-blue-600">{transfer.to_location}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm">{transfer.requested_by_name}</td>
                    <td className="py-3 px-4 text-sm max-w-xs truncate">{transfer.reason}</td>
                    <td className="py-3 px-4">{getStatusBadge(transfer.status)}</td>
                    <td className="py-3 px-4 text-sm">
                      {new Date(transfer.requested_at).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {user?.role === 'quality' && transfer.status === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleApprove(transfer.id)}
                              data-testid={`approve-transfer-${transfer.id}`}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Onayla
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedTransfer(transfer);
                                setShowRejectDialog(true);
                              }}
                              data-testid={`reject-transfer-${transfer.id}`}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Reddet
                            </Button>
                          </>
                        )}
                        {transfer.status === 'rejected' && transfer.rejection_reason && (
                          <span className="text-xs text-red-600">{transfer.rejection_reason}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {transfers.length === 0 && (
            <div className="text-center py-12 text-gray-600">
              Transfer kaydı bulunamadı
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Transfer Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yeni Transfer Talebi</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTransfer} className="space-y-4">
            <div className="space-y-2">
              <Label>Cihaz</Label>
              <Select value={newTransfer.device_id} onValueChange={(value) => setNewTransfer({ ...newTransfer, device_id: value })}>
                <SelectTrigger data-testid="transfer-device-select">
                  <SelectValue placeholder="Cihaz seçin" />
                </SelectTrigger>
                <SelectContent>
                  {devices.map((device) => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.id} - {device.type} ({device.location})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="to_location">Hedef Lokasyon</Label>
              <Input
                id="to_location"
                data-testid="transfer-location-input"
                placeholder="örn: Radyoloji Bölümü - 2. Kat"
                value={newTransfer.to_location}
                onChange={(e) => setNewTransfer({ ...newTransfer, to_location: e.target.value })}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="reason">Transfer Sebebi</Label>
              <Textarea
                id="reason"
                data-testid="transfer-reason-input"
                placeholder="Transfer talebinin sebebini açıklayın"
                value={newTransfer.reason}
                onChange={(e) => setNewTransfer({ ...newTransfer, reason: e.target.value })}
                rows={3}
                required
              />
            </div>
            
            <Button type="submit" className="w-full" data-testid="submit-transfer-btn">
              Transfer Talebi Oluştur
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Transfer Talebini Reddet</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="rejection-reason">Ret Nedeni</Label>
              <Textarea
                id="rejection-reason"
                data-testid="rejection-reason-input"
                placeholder="Transfer talebinin neden reddedildiğini açıklayın"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setShowRejectDialog(false)}>
                İptal
              </Button>
              <Button className="flex-1" onClick={handleReject} data-testid="confirm-reject-btn">
                Reddet
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Transfers;
