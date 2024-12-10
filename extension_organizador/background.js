let timeoutId;
const NOTIFICATION_DELAY = 500; // milisegundos de espera para agrupar notificaciones
const notificationQueue = new Set(); // Para evitar notificaciones duplicadas

chrome.downloads.onChanged.addListener(function(downloadDelta) {
  // Solo procesamos cuando la descarga está completa
  if (!downloadDelta.state || downloadDelta.state.current !== 'complete') return;

  clearTimeout(timeoutId);   // Cancela el timeout anterior si existe
  const downloadId = downloadDelta.id;   // ID de la descarga actual
  notificationQueue.add(downloadId);  // Agrega la descarga a la cola

  // Nuevo timeout para procesar las descargas en lote
  timeoutId = setTimeout(() => {
    processBatchDownloads(Array.from(notificationQueue));
    notificationQueue.clear();
  }, NOTIFICATION_DELAY);
});

function processBatchDownloads(downloadIds) {
  // Ntificación inicial
  chrome.notifications.create({
    type: "basic",
    iconUrl: "verificar.png",
    title: "Organizando descargas",
    message: "Procesando archivos..."
  });

  // Procesa todas las descargas
  chrome.downloads.search({id: downloadIds}, function(downloads) {
    const promises = downloads.map(download => 
      fetch('http://localhost:8000', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({file_path: download.filename})
      })
      .then(response => response.json())
    );

    // Procesa todas las respuestas juntas y sola notificación final
    Promise.all(promises)
      .then(results => {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "verificar.png",
          title: "Proceso completado",
          message: `${results.length} archivo(s) organizados`
        });
      })
      .catch(error => console.error('Error:', error));
  });
}