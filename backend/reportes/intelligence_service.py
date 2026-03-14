import math
from datetime import timedelta
from django.utils import timezone
from .models import Reporte
from django.db.models import Count, Avg

class IntelligenceService:
    @staticmethod
    def calculate_accumulation_velocity(report_count, days_period=30):
        """Calcula cuántos reportes nuevos aparecen por día en promedio."""
        return report_count / days_period if days_period > 0 else 0

    @staticmethod
    def project_future_risk(current_score, velocity, days_ahead, decay_rate=0.1):
        """
        Proyecta el riesgo futuro basándose en la velocidad de acumulación
        y una tasa de decaimiento (si hay limpieza activa).
        """
        # Modelo simple: Riesgo crece linealmente con la velocidad,
        # pero tiene un tope de saturación.
        future_score = current_score + (velocity * days_ahead)
        # Aplicamos un factor de saturación logarítmico para no explotar
        return current_score + math.log1p(future_score - current_score) if future_score > current_score else current_score

    @staticmethod
    def get_preventive_routes_hotspots(hotspots, threshold=0.8):
        """Filtra hotspots que requieren intervención preventiva inmediata."""
        return [h for h in hotspots if h['intensity'] >= threshold]

    @staticmethod
    def calculate_hotspots(reports_list, resolution=15, days_ahead=0):
        """Lógica central de cálculo de hotspots (refactorizada de la view)."""
        if not reports_list:
            return [], {}

        lats = [r.ubicacion.y for r in reports_list]
        lngs = [r.ubicacion.x for r in reports_list]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        lat_diff = max_lat - min_lat
        lng_diff = max_lng - min_lng
        lat_step = lat_diff / resolution if lat_diff > 0 else 0.001
        lng_step = lng_diff / resolution if lng_diff > 0 else 0.001
        
        grid = {}
        prioridad_pesos = {'urgente': 5.0, 'alta': 3.0, 'normal': 1.5, 'baja': 0.5}
        estado_pesos = {'nuevo': 2.0, 'proceso': 1.5, 'resuelto': 0.2, 'cerrado': 0.1}

        for r in reports_list:
            cell_x = math.floor((r.ubicacion.x - min_lng) / lng_step) if lng_step > 0 else 0
            cell_y = math.floor((r.ubicacion.y - min_lat) / lat_step) if lat_step > 0 else 0
            cell_x = min(max(cell_x, 0), resolution - 1)
            cell_y = min(max(cell_y, 0), resolution - 1)
            
            key = (cell_x, cell_y)
            peso_prio = prioridad_pesos.get(str(r.prioridad).lower(), 1.0)
            peso_est = estado_pesos.get(str(r.estado).lower(), 1.0)
            
            if key not in grid: grid[key] = {'score': 0, 'count': 0}
            grid[key]['score'] += peso_prio * peso_est
            grid[key]['count'] += 1

        if days_ahead > 0:
            total_count = len(reports_list)
            # Simplificación: usar una velocidad constante para el ejemplo
            global_velocity = (total_count / 30) # 1 reporte/día cada 30 total
            for key in grid:
                local_velocity = (grid[key]['count'] / total_count) * global_velocity * resolution
                grid[key]['score'] = IntelligenceService.project_future_risk(
                    grid[key]['score'], local_velocity, days_ahead
                )

        hotspots = []
        if grid:
            max_score = max(cell['score'] for cell in grid.values())
            for (cx, cy), data in grid.items():
                lat = min_lat + (cy + 0.5) * lat_step
                lng = min_lng + (cx + 0.5) * lng_step
                intensity = data['score'] / max_score if max_score > 0 else 0
                
                nivel = "bajo"
                if intensity > 0.7: nivel = "critico"
                elif intensity > 0.4: nivel = "alto"
                elif intensity > 0.2: nivel = "medio"
                
                hotspots.append({
                    "lat": lat,
                    "lng": lng,
                    "intensity": round(intensity, 3),
                    "score": round(data['score'], 1),
                    "risk_level": nivel,
                    "report_count": data['count']
                })

        metadata = {
            "resolution": resolution,
            "days_ahead": days_ahead,
            "min_lat": min_lat, "max_lat": max_lat,
            "min_lng": min_lng, "max_lng": max_lng
        }
        return hotspots, metadata
