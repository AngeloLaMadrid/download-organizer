let timeoutId;
const NOTIFICATION_DELAY = 500;
const notificationQueue = new Set();

chrome.downloads.onChanged.addListener(function(downloadDelta) {
  if (!downloadDelta.state || downloadDelta.state.current !== 'complete') return;

  clearTimeout(timeoutId);
  const downloadId = downloadDelta.id;
  notificationQueue.add(downloadId);

  timeoutId = setTimeout(() => {
    processBatchDownloads(Array.from(notificationQueue));
    notificationQueue.clear();
  }, NOTIFICATION_DELAY);
});

function processBatchDownloads(downloadIds) {
  // Procesar cada descarga individualmente
  const promises = downloadIds.map(id => 
    new Promise((resolve, reject) => {
      chrome.downloads.search({id: id}, function(downloads) {
        if (!downloads || !downloads.length) {
          reject(new Error(`No se encontró la descarga ${id}`));
          return;
        }

        const download = downloads[0];
        fetch('http://localhost:8000', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({file_path: download.filename})
        })
        .then(response => response.json())
        .then(resolve)
        .catch(reject);
      });
    })
  );

  Promise.all(promises)
    .then(results => {
      // Extraer las rutas de destino
      const destinations = results
        .map(result => result.destination)
        .filter(Boolean); // Eliminar valores nulos o undefined

      // Crear mensaje con las ubicaciones
      const locationsMessage = destinations
        .map(path => `• ${path}`)
        .join('\n');

      // Mostrar una única notificación
      chrome.notifications.create({
        type: "basic",
        iconUrl: "verificar.png",
        title: `${results.length} archivo(s) organizados`,
        message: locationsMessage || "No se pudo obtener la ubicación"
      });
    })
    .catch(error => {
      console.error('Error:', error);
      chrome.notifications.create({
        type: "basic",
        iconUrl: "error.png",
        title: "Error",
        message: "Ocurrió un error al organizar los archivos"
      });
    });
}