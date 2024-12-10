const mostrarDetalles = true; // Cambia a false para desactivar las impresiones

chrome.downloads.onChanged.addListener(function(downloadDelta) {
  if (downloadDelta.state && downloadDelta.state.current === 'complete') {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "verificar.png", // Asegúrate de que este archivo exista
      title: "Descarga Completada",
      message: "Tu descarga ha terminado"
    });

    // Notificar al servidor local
    chrome.downloads.search({id: downloadDelta.id}, function(downloads) {
      downloads.forEach(download => {
        if (mostrarDetalles) {
          console.log(`Archivo: ${download.filename}`);
          console.log(`Ruta: ${download.filename}`);
        }

        fetch('http://localhost:8000', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            file_path: download.filename
          })
        })
        .then(response => response.text())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));
      });
    });
  }
});