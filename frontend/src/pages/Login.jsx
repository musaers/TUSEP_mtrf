import { useState, useContext } from 'react';
import { AuthContext } from '../App';
import { API } from '../App';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Activity } from 'lucide-react';

const Login = () => {
  const { login } = useContext(AuthContext);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ name: '', email: '', password: '', role: 'health_staff' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, loginData);
      login(response.data.access_token, response.data.user);
      toast.success('Giriş başarılı!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/auth/register`, registerData);
      toast.success('Kayıt başarılı! Lütfen giriş yapın.');
      // Auto login after register
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: registerData.email,
        password: registerData.password
      });
      login(loginResponse.data.access_token, loginResponse.data.user);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kayıt başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-4">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">TÜSEP Dashboard</h1>
          <p className="text-gray-600">Tıbbi Cihaz Bakım Yönetim Sistemi</p>
        </div>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Hoş Geldiniz</CardTitle>
            <CardDescription>Hesabınıza giriş yapın veya yeni hesap oluşturun</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login" data-testid="login-tab">Giriş Yap</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">Kayıt Ol</TabsTrigger>
              </TabsList>

              <TabsContent value="login" data-testid="login-form">
                <form onSubmit={handleLogin} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">E-posta</Label>
                    <Input
                      id="login-email"
                      data-testid="login-email"
                      type="email"
                      placeholder="ornek@hastane.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Şifre</Label>
                    <Input
                      id="login-password"
                      data-testid="login-password"
                      type="password"
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="login-submit-btn"
                  >
                    {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" data-testid="register-form">
                <form onSubmit={handleRegister} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name">Ad Soyad</Label>
                    <Input
                      id="register-name"
                      data-testid="register-name"
                      type="text"
                      placeholder="Ahmet Yılmaz"
                      value={registerData.name}
                      onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email">E-posta</Label>
                    <Input
                      id="register-email"
                      data-testid="register-email"
                      type="email"
                      placeholder="ornek@hastane.com"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Şifre</Label>
                    <Input
                      id="register-password"
                      data-testid="register-password"
                      type="password"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-role">Rol</Label>
                    <Select value={registerData.role} onValueChange={(value) => setRegisterData({ ...registerData, role: value })}>
                      <SelectTrigger data-testid="register-role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="health_staff">Sağlık Personeli</SelectItem>
                        <SelectItem value="technician">Teknisyen</SelectItem>
                        <SelectItem value="manager">Yönetici</SelectItem>
                        <SelectItem value="quality">Kalite Birimi</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="register-submit-btn"
                  >
                    {loading ? 'Kayıt yapılıyor...' : 'Kayıt Ol'}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;