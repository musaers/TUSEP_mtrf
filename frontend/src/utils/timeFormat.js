/**
 * Saat cinsinden süreyi dakika:saniye formatına çevirir
 * @param {number} hours - Saat cinsinden süre
 * @returns {string} - "MM:SS" formatında string
 */
export const formatTimeMinutesSeconds = (hours) => {
  if (!hours || hours === 0) return "00:00";
  
  const totalSeconds = Math.floor(hours * 3600);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};

/**
 * Gerçek zamanlı timer için elapsed time hesaplar
 * @param {string|Date} startTime - Başlangıç zamanı
 * @returns {string} - "MM:SS" formatında string
 */
export const calculateElapsedTime = (startTime) => {
  if (!startTime) return "00:00";
  
  const start = typeof startTime === 'string' ? new Date(startTime) : startTime;
  const now = new Date();
  const diffMs = now - start;
  const diffSeconds = Math.floor(diffMs / 1000);
  
  const minutes = Math.floor(diffSeconds / 60);
  const seconds = diffSeconds % 60;
  
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};

/**
 * İki tarih arasındaki süreyi hesaplar (7/24)
 * @param {string|Date} startTime
 * @param {string|Date} endTime
 * @returns {string} - "MM:SS" formatında string
 */
export const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return "00:00";
  
  const start = typeof startTime === 'string' ? new Date(startTime) : startTime;
  const end = typeof endTime === 'string' ? new Date(endTime) : endTime;
  
  const diffMs = end - start;
  const diffSeconds = Math.floor(diffMs / 1000);
  
  const minutes = Math.floor(diffSeconds / 60);
  const seconds = diffSeconds % 60;
  
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};
