const NOTIFICATION_DELAY = 500;
const notificationQueue = new Set();
let timeoutId;

const getPathInfo = path => {
  const parts = path.split('\\');
  return {
    fileName: parts.pop(),
    folderName: parts.pop()
  };
};

chrome.downloads.onChanged.addListener(({id, state}) => {
  if (state?.current !== 'complete') return;
  
  clearTimeout(timeoutId);
  notificationQueue.add(id);
  timeoutId = setTimeout(async () => {
    try {
      const downloads = await Promise.all([...notificationQueue].map(async downloadId => {
        const [download] = await chrome.downloads.search({id: downloadId});
        if (!download) throw new Error(`Download ${downloadId} not found`);
        
        const response = await fetch('http://localhost:8000', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({file_path: download.filename})
        });
        return response.json();
      }));

      const message = downloads
        .map(data => {
          const {fileName, folderName} = getPathInfo(data.destination);
          return `Archivo: ${fileName}\nCarpeta: ${folderName}`;
        })
        .join('\n\n');

      chrome.notifications.create(`download-${Date.now()}`, {
        type: "basic",
        iconUrl: "verificar.png",
        title: "Archivos Organizados",
        message
      });
    } catch (error) {
      chrome.notifications.create(`error-${Date.now()}`, {
        type: "basic",
        iconUrl: "error.png",
        title: "Error",
        message: "Error al organizar los archivos"
      });
    }
    notificationQueue.clear();
  }, NOTIFICATION_DELAY);
});