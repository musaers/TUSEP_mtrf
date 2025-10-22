import { useState, useEffect, useContext } from 'react';
import { AuthContext, API } from '../App';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { Search, Users as UsersIcon, Award, XCircle } from 'lucide-react';

const Users = () => {
  const { user } = useContext(AuthContext);
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    const filtered = users.filter(u =>
      u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.role.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(filtered);
  }, [searchTerm, users]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
      setFilteredUsers(response.data);
    } catch (error) {
      toast.error('Kullanıcılar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const getRoleName = (role) => {
    const roleMap = {
      'health_staff': 'Sağlık Personeli',
      'technician': 'Teknisyen',
      'manager': 'Yönetici',
      'quality': 'Kalite Birimi'
    };
    return roleMap[role] || role;
  };

  const getRoleBadgeColor = (role) => {
    const colorMap = {
      'health_staff': 'bg-blue-100 text-blue-800',
      'technician': 'bg-amber-100 text-amber-800',
      'manager': 'bg-purple-100 text-purple-800',
      'quality': 'bg-green-100 text-green-800'
    };
    return colorMap[role] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="users-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Kullanıcılar</h1>
        <p className="text-gray-600">Sistem kullanıcıları ve performans metrikleri</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <Input
          placeholder="İsim, e-posta veya rol ile ara..."
          className="pl-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          data-testid="search-users-input"
        />
      </div>

      {/* Users Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredUsers.map((u) => (
          <Card key={u.id} className="metric-card" data-testid={`user-card-${u.email}`}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{u.name}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">{u.email}</p>
                  <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(u.role)}`}>
                    {getRoleName(u.role)}
                  </span>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <UsersIcon className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {u.role === 'technician' && (
                <div className="space-y-3 pt-3 border-t">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Award className="w-4 h-4 text-green-600" />
                      <span>Başarılı Onarım</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">{u.successful_repairs || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <XCircle className="w-4 h-4 text-red-600" />
                      <span>Başarısız Onarım</span>
                    </div>
                    <span className="text-sm font-semibold text-red-600">{u.failed_repairs || 0}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-sm text-gray-600">Başarı Oranı</span>
                    <span className="text-lg font-bold text-blue-600">
                      {u.successful_repairs + u.failed_repairs > 0
                        ? ((u.successful_repairs / (u.successful_repairs + u.failed_repairs)) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredUsers.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">Kullanıcı bulunamadı</p>
        </div>
      )}
    </div>
  );
};

export default Users;