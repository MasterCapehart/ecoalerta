import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { toast } from './ToastContainer';
import apiClient from '../services/api';

// Componente para manejar el zoom y centro del mapa
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

const EcoInteligenciaTab = () => {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolution, setResolution] = useState(15);
  const [daysAhead, setDaysAhead] = useState(0); // Nuevo: días a futuro
  const [mapCenter, setMapCenter] = useState([-29.9027, -71.2519]); // La Serena / Coquimbo
  const [metadata, setMetadata] = useState(null);

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/api/analytics/predicciones-espaciales/?resolution=${resolution}&days_ahead=${daysAhead}`);
      setHotspots(response.data.hotspots);
      setMetadata(response.data.metadata);
      
      if (response.data.hotspots.length > 0 && daysAhead === 0) {
        // Solo centramos si es la carga inicial o no estamos proyectando
        const first = response.data.hotspots[0];
        setMapCenter([first.lat, first.lng]);
      }
    } catch (error) {
      console.error('Error fetching predictive analytics:', error);
      toast.error('No se pudieron cargar las predicciones');
    } finally {
      setLoading(false);
    }
  }, [resolution, daysAhead]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  const getRiskColor = (level) => {
    switch (level) {
      case 'critico': return '#e74c3c';
      case 'alto': return '#f39c12';
      case 'medio': return '#f1c40f';
      default: return '#3498db';
    }
  };

  return (
    <div className="eco-inteligencia-container" style={{ height: 'calc(100vh - 150px)', display: 'flex', flexDirection: 'column' }}>
      <div className="eco-header" style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0 }}>🧠 Eco-Inteligencia: Mapa Predictivo</h2>
          <p style={{ margin: '5px 0', color: '#666' }}>
            Análisis de riesgo basado en densidad histórica, prioridad y tendencias IA.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '15px' }}>
          <div className="control-group" style={{ display: 'flex', alignItems: 'center', background: '#f0f2f5', padding: '5px 15px', borderRadius: '20px' }}>
            <label style={{ marginRight: '10px', fontSize: '13px', fontWeight: 'bold' }}>Proyección:</label>
            <input 
              type="range" 
              min="0" 
              max="14" 
              value={daysAhead} 
              onChange={(e) => setDaysAhead(Number(e.target.value))}
              style={{ width: '100px', cursor: 'pointer' }}
            />
            <span style={{ marginLeft: '10px', fontSize: '13px', color: daysAhead > 0 ? '#e67e22' : '#666', fontWeight: 'bold', minWidth: '60px' }}>
              {daysAhead === 0 ? 'Hoy' : `+ ${daysAhead} días`}
            </span>
          </div>

          <div className="control-group">
            <select 
              value={resolution} 
              onChange={(e) => setResolution(Number(e.target.value))}
              style={{ padding: '5px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value={10}>Baja Res.</option>
              <option value={15}>Normal</option>
              <option value={20}>Alta</option>
            </select>
          </div>
          <button 
            onClick={fetchPredictions}
            className="btn-refresh"
            style={{ padding: '5px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Refrescar
          </button>
        </div>
      </div>

      <div className="eco-content" style={{ flex: 1, display: 'flex', gap: '20px' }}>
        <div className="main-map-card" style={{ flex: 3, background: 'white', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', position: 'relative' }}>
          {loading && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(255,255,255,0.7)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <div className="spinner">Cargando Inteligencia...</div>
            </div>
          )}
          <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <MapController center={mapCenter} zoom={13} />
            
            {hotspots.map((spot, idx) => (
              <CircleMarker
                key={idx}
                center={[spot.lat, spot.lng]}
                radius={10 + (spot.intensity * 20)}
                fillColor={getRiskColor(spot.risk_level)}
                color="white"
                weight={2}
                opacity={0.8}
                fillOpacity={0.4 + (spot.intensity * 0.4)}
              >
                <Popup>
                  <div style={{ textAlign: 'center' }}>
                    <h4 style={{ margin: '0 0 5px 0', color: getRiskColor(spot.risk_level) }}>
                      Riesgo {spot.risk_level.toUpperCase()}
                    </h4>
                    <p style={{ margin: 0 }}>Probabilidad: <strong>{(spot.intensity * 100).toFixed(1)}%</strong></p>
                    <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>Basado en patrones de micro-basurales cercanos.</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        <div className="side-stats" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="stat-card" style={{ background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, fontSize: '16px' }}>Zonas Detectadas</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '24px', fontWeight: 'bold' }}>{hotspots.length}</span>
              <span style={{ color: daysAhead > 0 ? '#e67e22' : '#2ecc71', fontSize: '14px', fontWeight: 'bold' }}>
                {daysAhead > 0 ? 'Proyectadas' : 'Actuales'}
              </span>
            </div>
          </div>

          <div className="stat-card" style={{ background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', flex: 1 }}>
            <h3 style={{ marginTop: 0, fontSize: '16px' }}>Leyenda de Riesgo</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '15px', height: '15px', borderRadius: '50%', background: '#e74c3c' }}></div>
                <span>Crítico (Resolución Urgente)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '15px', height: '15px', borderRadius: '50%', background: '#f39c12' }}></div>
                <span>Alto (Intervención esta semana)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '15px', height: '15px', borderRadius: '50%', background: '#f1c40f' }}></div>
                <span>Medio (Monitoreo regular)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '15px', height: '15px', borderRadius: '50%', background: '#3498db' }}></div>
                <span>Estable (Zona bajo control)</span>
              </div>
            </div>
            <div style={{ marginTop: '30px', padding: '15px', background: '#f8f9fa', borderRadius: '8px', fontSize: '12px', color: '#555' }}>
              <strong>Nota:</strong> Estas predicciones ayudan a planificar rutas preventivas de recolección para evitar la proliferación de residuos.
              {metadata?.generated_at && (
                <div style={{ marginTop: '10px', fontSize: '10px', opacity: 0.7 }}>
                  Última actualización: {new Date(metadata.generated_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EcoInteligenciaTab;
