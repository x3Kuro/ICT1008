var map = null;
var i;

$(function() {
  $('button#submit').bind('click', function() {
    map.spin(true);
    $.getJSON('/data', {
      source: $('input[name="source"]').val(),
      dest: $('input[name="dest"]').val(),
      transport_mode: $('select[name="transport_mode"]').val()
    }, function(data) {
        map.spin(false);
        plotMap(data.train_path, data.walk_path, data.start, data.start_road, data.end, data.end_road);
      });
    return false;
  });
});

function plotMap(train_path, walk_path, src, start_rd, dest, end_rd) {
    if (map != undefined && map != null) {
        map.remove();
    }

    map = L.map('map', {
        fullscreenControl: true,
        fullscreenControlOptions: {
            position: 'topright'
      }
    }).setView([1.4052, 103.9024], 18);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    if (src != undefined && src != null){
        var src_marker = L.marker(src).addTo(map)
            .bindPopup(start_rd)
    }
    if (dest != undefined && dest != null){
        L.marker(dest, {
            icon: L.AwesomeMarkers.icon({
                icon: 'bullseye',
                prefix: 'fa',
                markerColor: 'green'
            })
        }).addTo(map)
            .bindPopup(end_rd)
    }

    var paths = L.featureGroup();
    paths.addTo(map);

    if (walk_path != undefined){
        for (var i=0; i < walk_path.length; i++){
            var walk_line = L.polyline(walk_path[i], {
                opacity: 0,
                smoothFactor: 1
            }).addTo(paths);
            L.polylineDecorator(walk_line, {
                patterns: [
                    // dash lines every 18px, for 1px size
                    {offset: 0, repeat: 18, symbol: L.Symbol.dash({pixelSize: 1, pathOptions: {color: '#0072d9', weight:10}})}
                ]
            }).addTo(paths);
        }
    }

    if (train_path != undefined){
        for (var i = 0; i < train_path.length; i++){
            L.polyline(train_path[i], {
                color:'red',
                width: 8,
                opacity: 1,
                smoothFactor: 1
            }).addTo(paths);
        }
    }

    // Ensure map shows the full route in start zoom
    map.fitBounds(paths.getBounds());

}
