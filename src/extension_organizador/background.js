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
        .then(response => {
          if (!response.ok) {
            throw new Error(`Error en la respuesta del servidor: ${response.statusText}`);
          }
          return response.json();
        })
        .then(resolve)
        .catch(reject);
      });
    })
  );

  Promise.all(promises)
    .then(results => {
      const destinations = results
        .map(result => result.destination)
        .filter(Boolean);

      const locationsMessage = destinations
        .map(path => `• ${path}`)
        .join('\n');

      const getFolderName = (path) => {
        const parts = path.split('\\');
        return parts[parts.length - 2];
      };
      
      chrome.notifications.create({
        type: "basic",
        iconUrl: "verificar.png",
        title: `${results.length} archivo(s) organizados`,
        message: destinations.map(path => {
          const folderName = getFolderName(path);
          const fileName = path.split('\\').pop();
          return `Archivo: "${fileName}"\nEnviado a: "${folderName}"`;
        }).join('\n\n')
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