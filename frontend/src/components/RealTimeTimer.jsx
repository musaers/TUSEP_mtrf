import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { calculateElapsedTime } from '../utils/timeFormat';

const RealTimeTimer = ({ startTime, endTime, className = "" }) => {
  const [elapsed, setElapsed] = useState("00:00");
  
  useEffect(() => {
    // Eğer bitiş zamanı varsa, statik süreyi göster
    if (endTime) {
      setElapsed(calculateElapsedTime(startTime));
      return;
    }
    
    // Başlangıç zamanı yoksa gösterme
    if (!startTime) {
      setElapsed("00:00");
      return;
    }
    
    // Her saniye güncelle
    const updateTimer = () => {
      setElapsed(calculateElapsedTime(startTime));
    };
    
    // İlk güncelleme
    updateTimer();
    
    // Her saniye güncelle
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [startTime, endTime]);
  
  const isActive = startTime && !endTime;
  
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <Clock className={`w-4 h-4 ${isActive ? 'text-blue-600 animate-pulse' : 'text-gray-600'}`} />
      <span className={`font-mono text-sm ${isActive ? 'text-blue-600 font-semibold' : 'text-gray-700'}`}>
        {elapsed}
      </span>
      {isActive && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
        </span>
      )}
    </div>
  );
};

export default RealTimeTimer;
