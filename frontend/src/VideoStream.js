import { useRef, useState } from 'react';

const VideoStream = ({ videoUrl, clickEndpoint }) => {
  const videoRef = useRef(null);
  const [isAutoMode, setIsAutoMode] = useState(true);
  const [isConfigMode, setIsConfigMode] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

  const sendCommand = async (endpoint, body) => {
    try {
      const response = await fetch(`${backendUrl}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      return await response.json();
    } catch (error) {
      console.error(`Erro ao enviar comando para ${endpoint}:`, error);
    }
  };

  // Se quiser, pode duplicar toggleMode para os 2 streams, por simplicidade aqui só um exemplo:
  const handleToggleAutoMode = async () => {
    // ... você pode modificar para aceitar parâmetros e endpoints diferentes
    // Para dois streams distintos, seria bom criar toggle automode por stream
  };

  const handleVideoClick = (event) => {
    if (!videoRef.current) return;
    const rect = videoRef.current.getBoundingClientRect();
    const x = Math.round(event.clientX - rect.left);
    const y = Math.round(event.clientY - rect.top);
    const naturalWidth = videoRef.current.naturalWidth || 1;
    const displayWidth = rect.width;
    const scale = naturalWidth / displayWidth;
    const scaledX = Math.round(x * scale);
    const scaledY = Math.round(y * scale);
    console.log(`Clique enviado para ${clickEndpoint}: (${scaledX}, ${scaledY})`);
    sendCommand(clickEndpoint, { x: scaledX, y: scaledY });
  };

  return (
    <div style={{ textAlign: 'center', padding: 10, color: 'white' }}>
      <img
        ref={videoRef}
        src={videoUrl}
        alt="Video Stream"
        onClick={handleVideoClick}
        style={{ cursor: 'crosshair', maxWidth: '90%', maxHeight: '60vh', border: '2px solid white' }}
      />
    </div>
  );
};

export default VideoStream;
