import React from 'react';
import Joyride, { STATUS } from 'react-joyride';
import apiClient from '../services/api';

const DashboardTour = ({ run, setRun, usuario, onTourComplete }) => {

    const steps = [
        {
            target: '.dashboard-container',
            content: '¡Bienvenido al Nuevo Dashboard Municipal de UrbanAlert! Vamos a darte un rápido recorrido por las principales herramientas operativas.',
            placement: 'center',
            disableBeacon: true,
        },
        {
            target: '.sidebar-nav',
            content: 'Este es tu Menú Principal. Desde aquí puedes navegar entre el Listado de Reportes, Mapas de Calor, Asignaciones, y el Centro de Operaciones en Vivo.',
            placement: 'right',
        },
        {
            target: '.recent-reports-card',
            content: 'Feed de Incidentes: Aquí verás los reportes más recientes que necesitan tu atención. Puedes hacer clic para gestionarlos rápidamente.',
            placement: 'left',
        },
        {
            target: '.stats-grid-enterprise',
            content: 'Métricas Clave: Monitorea las denuncias totales, la tasa de resolución y cómo rinden las cuadrillas en tiempo real.',
            placement: 'bottom',
        },
        {
            target: '.quick-filters-section',
            content: 'Filtros Rápidos: Búsqueda ágil y clasificación de incidentes por estado, prioridad o categoría sin recargar la página.',
            placement: 'bottom',
        },
        {
            target: '.btn-export-quick',
            content: 'Exportaciones y Reportes: Aquí podrás descargar estadísticas en PDF/Excel para reuniones ejecutivas.',
            placement: 'left',
        }
    ];

    const handleJoyrideCallback = async (data) => {
        const { status } = data;
        const finishedStatuses = [STATUS.FINISHED, STATUS.SKIPPED];

        // Si el tour se terminó o el usuario lo saltó explícitamente y era un recorrido real (no de "Ayuda")
        if (finishedStatuses.includes(status)) {
            setRun(false);

            // Llamar al backend para guardar que este usuario ya hizo el tour permanentemente si aún no lo tiene
            if (usuario && !usuario.tour_completado) {
                try {
                    await apiClient.post('/api/admin/usuarios/completar-tour/');
                    // Actualizamos el contexto de Auth local (refrescando los datos)
                    if (onTourComplete) onTourComplete();
                } catch (error) {
                    console.error('Error al guardar el estado del tour en BD:', error);
                }
            }
        }
    };

    return (
        <Joyride
            callback={handleJoyrideCallback}
            continuous
            hideCloseButton
            run={run}
            scrollToFirstStep
            showProgress
            showSkipButton
            steps={steps}
            styles={{
                options: {
                    zIndex: 10000,
                    primaryColor: '#3b82f6', // Azul de tailwind (igual al theme ecoalerta)
                    textColor: '#334155',
                    backgroundColor: '#ffffff',
                    overlayColor: 'rgba(0, 0, 0, 0.6)',
                },
                buttonNext: {
                    backgroundColor: '#3b82f6',
                    borderRadius: '6px',
                },
                buttonBack: {
                    marginRight: 10,
                    color: '#64748b',
                },
                buttonSkip: {
                    color: '#94a3b8',
                }
            }}
            locale={{
                back: 'Anterior',
                close: 'Cerrar',
                last: 'Finalizar',
                next: 'Siguiente',
                skip: 'Saltar Tour',
            }}
        />
    );
};

export default DashboardTour;
