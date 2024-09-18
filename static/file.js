map.on('click', function(e) {
   // Получаем координаты щелчка
   var lat = e.latlng.lat;
   var lng = e.latlng.lng;

   // Создаем новый маркер
   var marker = L.marker([lat, lng]).addTo(map);

   // Добавляем всплывающее окно для нового маркера
   marker.bindPopup("Новая точка!").openPopup();
});
// Импортируем плагин рисования
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw/dist/leaflet.draw.js';

// Инициализируем плагин рисования
var drawControl = new L.Control.Draw({
    edit: {
        featureGroup: drawnItems
    }
});
map.addControl(drawControl);

// Добавляем обработчик событий создания для форм рисования
map.on('draw:created', function(e) {
    var type = e.layerType;
    var layer = e.layer;

    // Сохраняем нарисованную форму на сервер (не показано в этом примере)
});
